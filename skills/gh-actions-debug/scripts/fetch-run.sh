#!/usr/bin/env bash
# fetch-run.sh - Fetch all GitHub Actions run data in one shot.
#
# Usage: bash scripts/fetch-run.sh <owner> <repo> <run_id> <output_dir>
#
# Produces in <output_dir>:
#   run.json       - Run metadata
#   jobs.json      - All jobs with name, conclusion, id, and failed steps
#   job.log        - Full log of the first failed job
#   errors.txt     - Error lines extracted from job.log
#   workflow.yml   - The workflow definition YAML
#
# Dependencies: gh (with --jq support)

set -euo pipefail

if [ $# -ne 4 ]; then
  echo "Usage: bash fetch-run.sh <owner> <repo> <run_id> <output_dir>"
  exit 1
fi

OWNER="$1"
REPO="$2"
RUN_ID="$3"
OUT_DIR="$4"

REPO_REF="$OWNER/$REPO"

mkdir -p "$OUT_DIR"

# Run metadata
gh run view "$RUN_ID" --repo "$REPO_REF" \
  --json name,headBranch,headSha,status,conclusion,url,workflowName,event \
  > "$OUT_DIR/run.json"

# Jobs list with failed steps
gh api "repos/$REPO_REF/actions/runs/$RUN_ID/jobs" \
  --jq '[.jobs[] | {name, conclusion, id, steps: [.steps[]? | select(.conclusion=="failure") | {name, number}]}]' \
  > "$OUT_DIR/jobs.json"

# Logs for the first failed job (use --log-failed to scope to failed steps)
gh run view "$RUN_ID" --repo "$REPO_REF" --log-failed > "$OUT_DIR/job.log"

# Extract error lines
{ grep -n '::error::\|\[error\]\|exit code [^0]\|Error:' "$OUT_DIR/job.log" || true; tail -20 "$OUT_DIR/job.log"; } > "$OUT_DIR/errors.txt"

# Workflow YAML
WORKFLOW_NAME=$(gh run view "$RUN_ID" --repo "$REPO_REF" --json workflowName --jq '.workflowName')
WPATH=$(gh api "repos/$REPO_REF/actions/workflows" --jq "[.workflows[] | select(.name==\"$WORKFLOW_NAME\") | .path][0]")
gh api "repos/$REPO_REF/contents/$WPATH" --jq '.content' | base64 -d > "$OUT_DIR/workflow.yml"

echo "FETCH DONE: run $RUN_ID → $OUT_DIR"
