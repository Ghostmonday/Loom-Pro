# Runbook

## Regenerate everything

```bash
cd loom-frontend-formation-corrected
python scripts/create_sources.py
python scripts/create_extensions.py
python scripts/build.py
python scripts/browser_check.py
```

## Validate all screens

```bash
PYTHONPATH=frontend-formation \
python -m validator.cli.main \
  --project .generated/loom/frontend-formation.all.yaml \
  --spec-dir frontend-formation/specification \
  --format json
```

## Run toolchain regression tests

```bash
cd frontend-formation
PYTHONPATH=. pytest -q
```

## Inspect reports

```text
reports/validation-summary.json
reports/node-check.json
reports/css-check.json
reports/browser-check.json
reports/generation.json
```
