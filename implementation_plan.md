# Implementation Plan — Interactive Vision Canvas UI Interrogation (Final)

This plan details the changes required to transition the Loom Vision Canvas into a first-class interactive user interrogation interface using native text entry controls and a distinct production API transport.

## User Review Required

> [!IMPORTANT]
> To support text entry controls as first-class manifest nodes, we will modify the Frontend Formation compiler schema and the validator rules to introduce the `input_control` classification.
>
> We will also update the build script `build.py` to default to `api-driver.js` (real API client) for normal and local builds, and load `mock-driver.js` only under explicit test/demo settings.

## 1. Schema & Manifest Changes

### [MODIFY] [screen-manifest.schema.json](file:///home/ghostmonday/Desktop/Loom/loom-frontend-base/frontend-formation/specification/screen-manifest.schema.json)
- Add `"input_control"` to the allowed elements classification enum on line 43:
  ```json
  "classification": {"enum": ["action_control", "display", "presentation", "input_control"]}
  ```
- Add `"input"` and `"textarea"` to the allowed elements tag enum on line 48:
  ```json
  "tag": {"enum": ["button", "div", "section", "aside", "header", "footer", "p", "span", "output", "input", "textarea"]}
  ```
- Add the `allOf` conditional definition requiring `input_control` elements to specify `contract_path` and a tag of `input` or `textarea`:
  ```json
  {
    "if": {"properties": {"classification": {"const": "input_control"}}, "required": ["classification"]},
    "then": {"required": ["contract_path", "tag"]}
  }
  ```

### [MODIFY] [r003_element_mapping.py](file:///home/ghostmonday/Desktop/Loom/frontend-formation-complete/frontend-formation/validator/rules/r003_element_mapping.py)
- Include `"input_control"` in `VALID_CLASSIFICATIONS`:
  ```python
  VALID_CLASSIFICATIONS = {"action_control", "display", "presentation", "input_control"}
  ```

### [MODIFY] [generator/core.py](file:///home/ghostmonday/Desktop/Loom/frontend-formation-complete/frontend-formation/generator/core.py)
- Update HTML rendering block to support `input_control`:
  - When classification is `input_control`, map properties (`placeholder`, `disabled`, `readonly`).
  - Generate an associated `<label for="[id]">[label]</label>` wrapping or preceding the `<textarea>`/`<input>` tag to satisfy accessibility rules.

### [MODIFY] [actions.registry.yaml](file:///home/ghostmonday/Desktop/Loom/loom-frontend-base/examples/loom-source/actions.registry.yaml)
- Add the explicit `question.finalize` action representing the request-finalization step:
  ```yaml
  question.finalize:
    description: Validate the session blueprint state and request transition to FINAL_CONFIRMATION status.
    lifecycle_states: *id001
    backend_endpoint: POST /api/v1/intent-forge/sessions/{session_id}/finalize
  ```

### [MODIFY] [vision-canvas.manifest.yaml](file:///home/ghostmonday/Desktop/Loom/loom-frontend-base/examples/loom-source/vision-canvas.manifest.yaml)
- Define separate first-class manifest nodes for prompt, question, answer, history, and revision:
  ```yaml
  - id: vision-prompt-input
    classification: input_control
    contract_path: loom.vision.prompt
    tag: textarea
    label: Express your software vision
  - id: vision-prompt-summary
    classification: display
    contract_path: loom.vision.prompt
    tag: div
    label: Current Vision
  - id: vision-question-display
    classification: display
    contract_path: loom.vision.current_question
    tag: div
    label: Interrogation Question
  - id: vision-answer-input
    classification: input_control
    contract_path: loom.vision.current_question
    tag: textarea
    label: Your Answer
  - id: vision-history-display
    classification: display
    contract_path: loom.vision.understanding
    tag: div
    label: Submitted Answers History
  - id: vision-revision-editor
    classification: input_control
    contract_path: loom.vision.understanding
    tag: textarea
    label: Edit Answer for Revision
  - id: vision-finalize-btn
    classification: action_control
    action: question.finalize
    feedback_target: vision-feedback
    label: Request Finalization
  ```

---

## 2. Decouple Driver Loading in `build.py`

### [MODIFY] [build.py](file:///home/ghostmonday/Desktop/Loom/loom-frontend-base/scripts/build.py)
- Change default behavior to load `api-driver.js`:
  ```python
  env_val = os.environ.get("LOOM_ENV", "").strip().lower()
  use_mock = os.environ.get("LOOM_USE_MOCK_DRIVER", "").strip() in {"1", "true", "yes"} or env_val in {"test", "demo"}
  driver_name = "mock-driver.js" if use_mock else "api-driver.js"
  ```
- Copy the selected driver file to the output directory as `mock-driver.js` (to preserve generation assembly tags without changing downstream pipeline names).

---

## 3. Real Backend Lifecycle & Endpoint Mapping

`api-driver.js` will map actions to the actual backend state machine as follows:

| UI Control / Action ID | Valid Session Statuses | API Endpoint Called | Request Payload | Response Fields Consumed | UI Enablement Conditions | Resulting Expected Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Start Intent Forge**<br>`intake.start_session` | None, `CREATED` | `POST /api/v1/intent-forge/sessions` | `{"prompt": "<prompt>", "tier": "paid"}` | `session_id`, `session_status`, `current_question`, `blueprint_version` | Prompt input textarea is not empty. | `QUESTIONING` |
| **Submit Answer**<br>`question.submit_answer` | `QUESTIONING`, `CONFLICT_RESOLUTION` | `POST /api/v1/intent-forge/sessions/{id}/answers` | `{"question_id": "<id>", "answer": "<answer>", "expected_blueprint_version": <version>}` | `session_status`, `current_question`, `blueprint_version`, `latest_analysis` | Answer input textarea is not empty and a question is active. | `QUESTIONING`, `CONFLICT_RESOLUTION`, or `VALIDATING` |
| **Request Finalization**<br>`question.finalize` | `QUESTIONING`, `VALIDATING` | `POST /api/v1/intent-forge/sessions/{id}/finalize` | `{"expected_blueprint_version": <version>, "force": false}` | `session_status`, `current_question`, `blueprint_version` | Active session exists. | `FINAL_CONFIRMATION` |
| **Confirm Handoff**<br>`handoff.confirm` | `FINAL_CONFIRMATION` | `POST /api/v1/intent-forge/sessions/{id}/handoff` | `{"action": "confirm", "expected_blueprint_version": <version>}` | `session_status`, `blueprint_version`, `artifact` | Session status is `FINAL_CONFIRMATION`. | `FINALIZED` |
| **Accept Handoff**<br>`handoff.accept` | `FINALIZED` | `POST /api/v1/intent-forge/sessions/{id}/handoff` | `{"action": "accept", "expected_blueprint_version": <version>}` | `session_status`, `blueprint_version` | Session status is `FINALIZED`. | `HANDED_OFF` |

---

## 4. Input & Revision Rules

- **Input checks**: Disable action control buttons immediately if prompt/answer values are empty. Do not perform network requests.
- **Revision workflow**:
  - `vision-history-display` renders a list of past questions and answers with a selection trigger (radio/buttons).
  - Selecting a past item populates its text into `vision-revision-editor` and stores its `question_id` in a data attribute.
  - Clicking `Revise Previous Answer` retrieves the ID from the attribute and the edited value from `vision-revision-editor`, posting them to `/revise`.
- **Local Storage**:
  - Store temporary draft text on `input` events to prevent data loss on reload.
  - Do **not** use local storage value as the authoritative source of session status, version, or readiness. Rely entirely on the backend payload response.

---

## 5. Transport Requirements

- **Headers**:
  - `Content-Type: application/json`
  - `X-User-Id` (retrieved from localStorage/config)
  - `X-Loom-Api-Key` (retrieved from localStorage/config)
- **Payload Params**:
  - Mutating requests must generate a fresh UUID for `idempotency_key`.
  - Mutating requests must include the current `expected_blueprint_version`.
- **Error Handling**:
  - `409 Version Conflict`: Prompt user to reload/refresh the local state view.
  - Duplicate Idempotency / Validation Errors: Render description inside the `vision-feedback` element.

---

## 6. Verification Plan

### Automated Tests

#### [NEW] [test_driver_selection.py](file:///home/ghostmonday/Desktop/Loom/tests/test_driver_selection.py)
- Verify that a standard build (`python scripts/build.py` with no environment variables) generates a build containing the `api-driver.js` payload and does not contain the hardcoded mock/fixture steps.

#### [NEW] [test_live_vision_canvas.py](file:///home/ghostmonday/Desktop/Loom/tests/test_live_vision_canvas.py)
- Spawns the uvicorn API server and runs a Playwright test sequence:
  1. Types a vision into `vision-prompt-input`.
  2. Clicks `Start`. Verifies request is sent and status transitions to `QUESTIONING`.
  3. Verifies backend question is shown in `vision-question-display`.
  4. Types an answer in `vision-answer-input` and clicks `Submit`. Verifies answer reaches endpoint.

#### [MODIFY] [browser_check.py](file:///home/ghostmonday/Desktop/Loom/loom-frontend-base/scripts/browser_check.py)
- Update mock routes to intercept `/answers`, `/revise`, `/finalize`, and `/handoff` to return valid mock JSONs containing real interrogation progress.
- Assert that clicking `Start` with an empty prompt textarea raises a rejection / causes no HTTP requests.
