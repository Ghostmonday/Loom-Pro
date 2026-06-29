#!/bin/bash
set -e

# Make sure we are in the repository root
cd "$(dirname "$0")/.."

echo "==> Pushing current branch 'codex/p3-authority-enforcement' to origin..."
git push origin codex/p3-authority-enforcement

echo "==> Creating the new Pull Request..."
gh pr create \
  --title "PR 38 Remediations: Seal semantic authority, reflect dark curvature edges, and session-bind overrides" \
  --body-file pr_description.md \
  --head codex/p3-authority-enforcement \
  --base main

echo "==> Closing PR 36..."
gh pr close 36 --delete-branch || echo "Warning: Could not close PR 36 or delete its branch."

echo "==> Closing PR 38..."
gh pr close 38 --delete-branch || echo "Warning: Could not close PR 38 or delete its branch."

echo "==> PR creation and cleanup completed successfully!"
