#!/usr/bin/env bash
# pilot - one-click PR creation with idempotent resume.
# Usage: pilot.sh <state-dir> <base> <new-branch> <wt-name> <wt-path>
#                 <commit-msg> <pr-title> <pr-body> [files...]
#
# Runs in order: tool_check → create_worktree → copy_files → commit → push → create_pr.
# Each completed step writes a marker to <state-dir>/state/done_<step>.
# Re-run with same args to resume from the first incomplete step.
# Prints PR URL on success, FAIL: <step> + reason on failure.
#
# <commit-msg>, <pr-title>, <pr-body> support @path prefix to read from file.
set -u

MIN_ARGS=8
if [ $# -lt $MIN_ARGS ]; then
  echo "pilot: usage: pilot.sh <state-dir> <base> <new-branch> <wt-name> <wt-path> <commit-msg> <pr-title> <pr-body> [files...]"
  exit 1
fi

STATE_DIR="$1"
BASE="$2"
NEW_BRANCH="$3"
WT_NAME="$4"
WT_PATH="$5"
COMMIT_MSG_ARG="$6"
PR_TITLE_ARG="$7"
PR_BODY_ARG="$8"
shift 8
FILES=("$@")

STATE_DIR="$STATE_DIR/state"
mkdir -p "$STATE_DIR" || { echo "pilot: cannot create state dir"; exit 1; }

# --- Helpers ------------------------------------------------------------------
step_done()   { [ -f "$STATE_DIR/done_$1" ]; }
step_mark()   { touch "$STATE_DIR/done_$1" || { echo "pilot: cannot write state marker"; exit 1; } }

# resolve_val <arg>: prints the value (literal, or file content if @path prefix).
resolve_val() {
  local v="$1"
  case "$v" in
    @*)
      local f="${v#@}"
      if [ ! -f "$f" ]; then
        echo "pilot: file not found: $f" >&2
        return 1
      fi
      cat -- "$f"
      ;;
    *)
      printf '%s' "$v"
      ;;
  esac
}

ROOT=""
ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "pilot: not inside a git repository"; exit 1; }

# --- Fail helper ---
fail() {
  echo "FAIL: $1"
  exit 1
}

# --- Step 1: tool_check -------------------------------------------------------
if ! step_done "01_tool_check"; then
  missing=""
  for tool in git gh; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      missing="$missing $tool"
    fi
  done
  if [ -n "$missing" ]; then
    fail "tool_check: missing tools:$missing"
  fi
  step_mark "01_tool_check"
fi

# --- Step 2: create_worktree --------------------------------------------------
if ! step_done "02_create_worktree"; then
  if git show-ref --verify --quiet "refs/heads/$NEW_BRANCH"; then
    fail "create_worktree: branch already exists: $NEW_BRANCH"
  fi
  if [ -e "$WT_PATH" ]; then
    fail "create_worktree: target path already exists: $WT_PATH"
  fi
  mkdir -p "$(dirname "$WT_PATH")" 2>/dev/null || true
  if ! git -C "$ROOT" worktree add -b "$NEW_BRANCH" "$WT_PATH" "$BASE"; then
    fail "create_worktree: git worktree add failed"
  fi
  step_mark "02_create_worktree"
fi

# --- Step 3: copy_files -------------------------------------------------------
if ! step_done "03_copy_files"; then
  if [ ${#FILES[@]} -eq 0 ]; then
    # If user explicitly passed empty file list, that's weird but not an error.
    # No files to copy means nothing will be in the worktree, which the user
    # would catch at the diff/scope step.
    :
  else
    for src in "${FILES[@]}"; do
      if [ ! -e "$src" ]; then
        fail "copy_files: source not found (cwd=$(pwd)): $src"
      fi
      # Compute destination in worktree
      dst="$WT_PATH/$src"
      dstparent=$(dirname -- "$dst")
      mkdir -p -- "$dstparent" || fail "copy_files: cannot mkdir $dstparent"

      if [ -d "$src" ]; then
        # Directory: copy recursively, preserving attributes.
        mkdir -p -- "$dst" || fail "copy_files: cannot mkdir $dst"
        # The trailing dot on source means "contents of src/".
        if ! cp -a -- "${src%/}/." "$dst/." 2>/dev/null && \
           ! cp -r -- "${src%/}/." "$dst/." 2>/dev/null; then
          fail "copy_files: cannot copy directory $src"
        fi
      elif [ -f "$src" ]; then
        cp -p -- "$src" "$dst" || fail "copy_files: cannot copy $src"
      else
        fail "copy_files: not a file or directory: $src"
      fi
    done
  fi
  step_mark "03_copy_files"
fi

# --- Step 4: commit -----------------------------------------------------------
if ! step_done "04_commit"; then
  MSG=$(resolve_val "$COMMIT_MSG_ARG") || fail "commit: bad commit-msg arg"
  if [ -z "$MSG" ]; then
    fail "commit: commit message is empty"
  fi
  # git add everything
  if ! git -C "$WT_PATH" add -A; then
    fail "commit: git add failed"
  fi
  # Check if anything staged
  if git -C "$WT_PATH" diff --cached --quiet 2>/dev/null; then
    fail "commit: nothing staged to commit — files may be identical to HEAD"
  fi
  # Commit using -F - for safe multi-line handling
  if ! printf '%s\n' "$MSG" | git -C "$WT_PATH" commit -F - --; then
    fail "commit: git commit failed"
  fi
  step_mark "04_commit"
fi

# --- Step 5: push -------------------------------------------------------------
if ! step_done "05_push"; then
  RETRIES=3
  push_ok=""
  for i in $(seq 1 "$RETRIES"); do
    if git -C "$WT_PATH" push -u origin "$NEW_BRANCH" 2>/dev/null; then
      push_ok=1
      break
    fi
    if [ "$i" -lt "$RETRIES" ]; then
      sleep 2
    fi
  done
  if [ -z "$push_ok" ]; then
    fail "push: failed after $RETRIES attempts (https). Try ssh or check credentials."
  fi
  step_mark "05_push"
fi

# --- Step 6: create_pr --------------------------------------------------------
if ! step_done "06_create_pr"; then
  TITLE=$(resolve_val "$PR_TITLE_ARG") || fail "create_pr: bad pr-title arg"
  BODY=$(resolve_val "$PR_BODY_ARG") || fail "create_pr: bad pr-body arg"
  if [ -z "$TITLE" ]; then
    fail "create_pr: PR title is empty"
  fi

  # Write body to a temp file for gh
  BODY_FILE=$(mktemp) || fail "create_pr: mktemp failed"
  trap 'rm -f -- "$BODY_FILE"' EXIT
  printf '%s' "$BODY" > "$BODY_FILE"

  if ! cd "$WT_PATH"; then
    fail "create_pr: cannot enter worktree: $WT_PATH"
  fi

  PR_URL=$(gh pr create --base "$BASE" --title "$TITLE" --body-file "$BODY_FILE" 2>&1)
  RC=$?
  rm -f -- "$BODY_FILE"
  trap - EXIT

  if [ $RC -ne 0 ]; then
    echo "pilot: gh pr create failed"
    echo "$PR_URL"
    fail "create_pr: gh error"
  fi

  echo "$PR_URL"
  step_mark "06_create_pr"
fi

echo "pilot: done"
exit 0
