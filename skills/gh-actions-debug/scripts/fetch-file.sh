#!/usr/bin/env bash
# fetch-file.sh - Fetch a specific file from a GitHub repo at a given ref.
#
# Usage: bash scripts/fetch-file.sh <owner> <repo> <path> [ref] [output_file]
#
# If ref is omitted, uses the default branch.
# If output_file is omitted, prints to stdout.
#
# Dependencies: gh

set -euo pipefail

if [ $# -lt 3 ] || [ $# -gt 5 ]; then
  echo "Usage: bash fetch-file.sh <owner> <repo> <path> [ref] [output_file]"
  exit 1
fi

OWNER="$1"
REPO="$2"
FILE_PATH="$3"
REF="${4:-}"
OUTPUT="${5:-}"

REPO_REF="$OWNER/$REPO"

API_URL="repos/$REPO_REF/contents/$FILE_PATH"
[ -n "$REF" ] && API_URL="$API_URL?ref=$REF"

if [ -n "$OUTPUT" ]; then
  gh api "$API_URL" --jq '.content' | base64 -d > "$OUTPUT"
  echo "Saved to $OUTPUT"
else
  gh api "$API_URL" --jq '.content' | base64 -d
fi
