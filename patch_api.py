path = "aoc_supervisor/aoc_supervisor/api.py"
content = open(path).read()

new_spawn = """            if mock_grid:
                with log_path.open("a", encoding="utf-8") as stdout_file:
                    proc = popen_worker_process(
                        cmd,
                        stdout=stdout_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        cwd=str(worker_dir.resolve()),
                    )
            else:
                stdout_file = log_path.open("a", encoding="utf-8")
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(worker_dir.resolve()),
                )
                if proc.stdout:
                    asyncio.create_task(
                        _read_stream(sprint_id, worker_name, manifest_detail.get("domain"), proc.stdout, stdout_file)
                    )"""

# Search for the block to replace
target_start = '            with log_path.open("a", encoding="utf-8") as stdout_file:'
target_end = '            worker_list.append({"name": worker_name, "status": "spawned", "pid": proc.pid})'

start_idx = content.find(target_marker if "target_marker" in locals() else target_start)
# Find the exact end of the popen_worker_process call
# It follows target_start and contains "cwd=str(worker_dir.resolve()),"
end_marker = "                cwd=str(worker_dir.resolve()),"
end_idx = content.find(end_marker, start_idx)
end_idx = content.find("            )", end_idx) + 1

# Verify we have the right block
print(f"Replacing from {start_idx} to {end_idx}")
# print(content[start_idx:end_idx])

new_content = content[:start_idx] + new_spawn + content[end_idx:]
with open(path, "w") as f: f.write(new_content)
