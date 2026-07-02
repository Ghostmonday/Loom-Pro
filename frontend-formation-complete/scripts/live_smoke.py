#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def _validate_http_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported URL scheme: {parsed.scheme!r}")


def http_request(url: str, **kwargs: Any) -> urllib.request.Request:
    _validate_http_url(url)
    return urllib.request.Request(url, **kwargs)  # noqa: S310


def urlopen_http(url_or_request: str | urllib.request.Request, **kwargs: Any):
    url = url_or_request.full_url if isinstance(url_or_request, urllib.request.Request) else url_or_request
    _validate_http_url(url)
    return urllib.request.urlopen(url_or_request, **kwargs)  # noqa: S310


def run_smoke_test():
    print("=== STARTING LIVE INTEGRATION SMOKE TEST ===")

    # 1. Start Loom's Uvicorn server in a subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/ghostmonday/Desktop/Loom/aoc-cli:/home/ghostmonday/Desktop/Loom/aoc_supervisor"
    env["GAIJINN_ALLOW_INSECURE_LOCAL"] = "1"
    env["GAIJINN_FAKE_REASONING"] = "1"
    env["LOOM_API_KEY"] = "mock_api_key_123"

    cmd = [
        "/home/ghostmonday/Desktop/Loom/.venv/bin/python",
        "-m",
        "uvicorn",
        "aoc_supervisor.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
    ]

    print(f"Launching Uvicorn server: {' '.join(cmd)}")
    server_proc = subprocess.Popen(  # noqa: S603
        cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Wait for the server to be up
    server_ready = False
    for i in range(20):
        time.sleep(0.5)
        try:
            with urlopen_http("http://127.0.0.1:8080/api/v1/health", timeout=1.0) as conn:
                if conn.status == 200:
                    server_ready = True
                    break
        except (urllib.error.URLError, TimeoutError, OSError):
            continue

    if not server_ready:
        print("ERROR: Uvicorn server failed to start or respond in time.")
        server_proc.terminate()
        stdout, stderr = server_proc.communicate()
        print("STDOUT:", stdout.decode())
        print("STDERR:", stderr.decode())
        sys.exit(1)

    print("Uvicorn server is up and healthy.")

    try:
        # 2. Serve the generated frontend through HTTP
        print("Checking if generated frontend is served via HTTP...")
        req = http_request("http://127.0.0.1:8080/vision_canvas/index.html")
        try:
            with urlopen_http(req) as conn:
                content = conn.read().decode("utf-8")
                assert "Loom Vision Canvas" in content or "loom.vision_canvas" in content
                print("SUCCESS: Generated frontend is successfully served through HTTP (found Vision Canvas markers).")
        except Exception as e:
            print(f"ERROR: Failed to serve generated frontend: {e}")
            raise

        # 3. Create a paid Intent Forge session
        print("Creating paid Intent Forge session...")
        create_url = "http://127.0.0.1:8080/api/v1/intent-forge/sessions"
        create_payload = {"prompt": "Build a secure audit ledger with auth", "tier": "paid"}
        create_headers = {
            "Content-Type": "application/json",
            "X-User-Id": "alice",
            "X-Loom-Api-Key": "mock_api_key_123",
        }

        req = http_request(
            create_url, data=json.dumps(create_payload).encode("utf-8"), headers=create_headers, method="POST"
        )

        with urlopen_http(req) as conn:
            session_data = json.loads(conn.read().decode("utf-8"))

        print("Response received from POST /sessions:")
        print(json.dumps(session_data, indent=2))

        # 4. Assertions on the created session
        session_id = session_data["session_id"]
        session_status = session_data["session_status"]
        current_question = session_data["current_question"]
        blueprint_version = session_data["blueprint_version"]

        assert session_status == "QUESTIONING", f"Expected session_status 'QUESTIONING', got '{session_status}'"
        assert isinstance(current_question, dict), "Expected current_question to be a structured dictionary"
        assert "question_id" in current_question, "Expected question_id in current_question"
        assert "text" in current_question, "Expected text in current_question"
        assert "domain" in current_question, "Expected domain in current_question"
        print("SUCCESS: current_question remains a full structured object.")

        question_id = current_question["question_id"]

        # 5. Submit an answer
        print(f"Submitting answer for question {question_id}...")
        answer_url = f"http://127.0.0.1:8080/api/v1/intent-forge/sessions/{session_id}/answers"
        answer_payload = {
            "question_id": question_id,
            "answer": "All modifications must be signed by the auditor key",
            "expected_blueprint_version": blueprint_version,
            "idempotency_key": "smoke_test_idempotency_001",
        }
        answer_headers = {
            "Content-Type": "application/json",
            "X-User-Id": "alice",
            "X-Loom-Api-Key": "mock_api_key_123",
        }

        req = http_request(
            answer_url, data=json.dumps(answer_payload).encode("utf-8"), headers=answer_headers, method="POST"
        )

        with urlopen_http(req) as conn:
            answer_response = json.loads(conn.read().decode("utf-8"))

        print("Response received from POST /answers:")
        print(json.dumps(answer_response, indent=2))

        # 6. Assertions on the answer response
        new_question = answer_response["current_question"]
        qa_history = answer_response.get("questions_and_answers", [])
        new_version = answer_response["blueprint_version"]

        # Check version advancement
        assert new_version > blueprint_version, (
            f"Expected version to advance from {blueprint_version}, got {new_version}"
        )
        print(f"SUCCESS: Blueprint version advanced successfully ({blueprint_version} -> {new_version}).")

        # Check answer inclusion in history
        found_answer = False
        for entry in qa_history:
            if entry.get("question_id") == question_id:
                assert entry.get("answer") == "All modifications must be signed by the auditor key"
                found_answer = True
                break
        assert found_answer, f"Answer history did not record answer for {question_id}"
        print("SUCCESS: Submitted answer is correctly recorded in questions_and_answers history.")

        # Check new question ID differs (or progress)
        if new_question:
            assert isinstance(new_question, dict)
            assert new_question["question_id"] != question_id, (
                "Expected next question ID to differ from prior question ID"
            )
            print(f"SUCCESS: Next question generated (ID: {new_question['question_id']}).")
        else:
            print("INFO: Session finalized or transitioned, no new question returned.")

        print("=== LIVE INTEGRATION SMOKE TEST COMPLETED SUCCESSFULLY ===")

    finally:
        print("Stopping Uvicorn server...")
        server_proc.terminate()
        server_proc.wait()


if __name__ == "__main__":
    run_smoke_test()
