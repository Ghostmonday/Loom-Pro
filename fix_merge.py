path = "aoc-cli/aoc_cli/commands/merge_grid.py"
content = open(path).read()
old = 'passing = sorted(worker_id for worker_id, result in validated.items() if result.get("passed") is True)'
new = 'passing = sorted(worker_id for worker_id, result in validated.items() if result.get("passed") is True or dry_run)'
content = content.replace(old, new)
with open(path, "w") as f: f.write(content)
