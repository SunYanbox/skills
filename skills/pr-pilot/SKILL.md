---
name: pr-pilot
description: >-
  One-click PR creation with project-aware AI generation. Use when: (1) "make a PR
  for these changes", (2) "turn this into a PR", (3) "commit and create a PR for
  src/core", (4) "create a PR with AI-generated message", (5) "automate my PR
  workflow", or (6) resume a paused pr-pilot task. Not for uncommitted scratch work
  — that's worktree-pr.
---

# pr-pilot

Turn a set of **changed files** into a clean pull request: analyze project
conventions, AI-generate branch name + commit message + PR content, then
bootstrap a throwaway worktree and create the PR in one scripted motion.

Mental model: user is on a branch with changes (committed or uncommitted).
This skill (1) learns the project's commit/PR style if it hasn't already,
(2) asks what to include, (3) reviews the diff, (4) AI-generates branch name,
commit message, PR title, and PR body aligned to project conventions, then
(5) runs a single script that worktrees, copies files, commits, pushes, and
creates the PR — all in one shot. Stops after PR creation; user waits for CI.

State persists under `.pr-pilot/` in the repo root.

## Tool Usage Policy (能力覆盖)

Decide tool choice by **capability coverage**, not blanket prohibitions:

| Operation type | Tool | Rule |
|---|---|---|
| Side effects (git/gh, complex ops) | `scripts/` bundled scripts via **Bash** | When `scripts/` has a script for the task, **must** use it. Never hand-roll equivalent command chains. |
| Status updates & non-script reads/writes | **Edit** / **Read** tools | Edit task doc, read files → use native tools directly. See `references/step-details.md`. |
| Pure file I/O (`cat`, `sed`, `grep`, `awk` on files) | **Read** / **Edit** / **Grep** tools | **Forbidden** via Bash when a native tool can do the job. |
| Git status queries (`diff`, `status`, `log`, `branch`) | **Bash** (allowed) | No native tool equivalent exists; Bash is the right choice. |

## Bundled Scripts

`<skill-dir>` = absolute path of the directory containing this `SKILL.md`.
Substitute it everywhere. All scripts print ASCII English to stdout, aimed at the Agent.
Success → exit 0; failure → non-zero + a short reason on stderr.

| Script | Args | What it does |
|---|---|---|
| `ghchk` | (none) | Exits 0 if `git` and `gh` are on PATH, else 1. |
| `pilot.sh` | `<state-dir> <base> <new-branch> <wt-name> <wt-path> <commit-msg> <pr-title> <pr-body> [files...]` | One-click PR creation. Runs tool check → create worktree → copy files → commit → push → create PR with idempotent resume. `commit-msg`/`pr-title`/`pr-body` support `@path` to read from file. See detailed usage below. |

### `pilot.sh` Usage

```bash
bash <skill-dir>/scripts/pilot.sh \
  ".pr-pilot" \
  "<base-branch>" \
  "<new-branch-name>" \
  "<wt-name>" \
  "<wt-path>" \
  "<commit-msg>" \
  "<pr-title>" \
  "<pr-body>" \
  "path/file1" "path/file2" ...
```

- `<base-branch>` — the branch this PR targets (e.g. `main`, `develop`)
- `<new-branch-name>` — full branch name for the PR (e.g. `feat/add-login`)
- `<wt-name>` — short unique name for the worktree (e.g. `a1b2`)
- `<wt-path>` — full path to the worktree (e.g. `.pr-pilot/worktrees/a1b2`)
- `<commit-msg>` — commit message, or `@.pr-pilot/temp/commit-msg.txt` to read from file
- `<pr-title>` — PR title, or `@.pr-pilot/temp/pr-title.txt`
- `<pr-body>` — PR body, or `@.pr-pilot/temp/pr-body.txt`
- `files...` — file/dir paths (relative to repo root) to copy into the worktree

**Resume**: `pilot.sh` checks `.pr-pilot/state/done_*` markers. Re-run with the same args to skip completed steps. It does NOT clean up on failure — leaves partial state for resume.

## State Files (`.pr-pilot/`)

```
.pr-pilot/
├── .gitignore          # contents: *
├── preferences.md      # Project preferences (see below)
├── state/              # Script completion markers: done_01_tool_check, etc.
├── temp/               # Agent temp files (commit messages, PR bodies)
└── worktrees/          # Git worktrees (created by pilot.sh or git)
```

### preferences.md Schema

```
- 分支格式: <branch-naming-pattern>     # Required, e.g. feat/<short-desc>, fix/<short-desc>
- 提交语言: <中文|英文>                  # Required
- PR语言: <中文|英文>                    # Required
- 提交格式: <commit-style-description>   # Optional, e.g. "Conventional Commits"
- PR格式: <pr-style-description>        # Optional
- PR模板路径: <path-to-template>        # Optional
- 其他偏好: <free-form-prose>           # Optional
```

For detailed resolution rules, see `references/preferences.md`.

## The Workflow

Run steps in order. [ ] = checkboxes for you to tick as you go.

### Step 0 — Initialize & resume check

- [ ] Determine current branch: `git rev-parse --abbrev-ref HEAD`
- [ ] Check if `.pr-pilot/` exists. If not, init:
  ```bash
  mkdir -p .pr-pilot/state .pr-pilot/temp
  printf '*\n' > .pr-pilot/.gitignore
  ```
- [ ] Scan `.pr-pilot/state/` for `done_*` markers.

**Resume logic**: If any `done_*` markers exist, the script had already completed some steps before interruption. Read `.pr-pilot/temp/` for previously generated content files. Ask the user if they want to resume the interrupted task or start fresh. If resume → proceed to Step 1 (preferences may already exist) and then skip straight to Step 5 (the script will handle idempotency). If fresh → `rm -rf .pr-pilot/state .pr-pilot/temp` then re-init.

### Step 1 — 项目偏好 (Project Preferences)

*Purpose: Establish or refresh the project's conventions for branches, commits, and PRs.*

- [ ] Check if `.pr-pilot/preferences.md` exists and has all required keys (`分支格式`, `提交语言`, `PR语言`)
- [ ] If all required keys present → ask user: "Project preferences found. Use them as-is, or review/update?" If "as-is" → skip to Step 2
- [ ] If missing or user wants review → analyze:

  ```bash
  # 1. Commit style: last 30 commits
  git log --oneline -30

  # 2. Branch style: existing branches
  git branch -a | head -30
  git for-each-ref --format='%(refname:short)' refs/heads refs/remotes | head -30

  # 3. PR style: recent PRs (if gh is available)
  gh pr list --state all --limit 10 --json number,title,body,headRefName 2>/dev/null || echo "(gh not available, skip PR analysis)"
  # For each PR, optionally: gh pr view <num> --json title,body
  ```

- [ ] Summarize observations to user in natural language, e.g.:
  > "Based on analysis:
  > - **Branch format**: `feat/<desc>` and `fix/<desc>` are common
  > - **Commit style**: Conventional Commits in Chinese (feat, fix, refactor types)
  > - **PR language**: Chinese titles and bodies
  > Does this match your project's conventions? Any adjustments?"

- [ ] Wait for user confirmation or corrections
- [ ] Write `.pr-pilot/preferences.md` with confirmed values. If file exists but user just adjusted specific keys, use Edit tool to update only those keys.
- [ ] **Record in memory** — save `project` memory about project's Git/PR conventions so future sessions skip re-analysis. Use a descriptive name like `project-git-conventions`.

### Step 2 — 指定范围 (Specify Scope)

*Purpose: Determine which files go into this PR.*

- [ ] Ask user which files/changes to include
- [ ] Prompt examples: "What would you like to include in this PR? All changes, specific files, or a directory?"
- [ ] If user says "all changes" or equivalent → run `git diff --name-only HEAD` (if uncommitted) or `git diff --name-only <base>...HEAD` (if on a branch with commits).
- [ ] If user specifies specific files/dirs → confirm the list before proceeding. If cannot resolve confidently → ask, do not guess.
- [ ] Record the scope as a list of paths relative to repo root.

### Step 3 — 对比差异 (Compare Diff)

*Purpose: Understand what changed so you can write accurate content.*

- [ ] For the scoped files, capture the full diff:
  ```bash
  # If uncommitted changes:
  git diff HEAD -- <files...>
  # If on a branch with commits:
  git diff <base>...HEAD -- <files...>
  # Combined:
  git diff HEAD -- <files...> ; git diff --cached -- <files...>
  ```
- [ ] Review the diff — note every file added/modified/deleted and every functional change.
- [ ] If diff is empty → tell user, check if they meant something else, or stop.

### Step 4 — 生成内容 (Generate Content)

*Purpose: AI-generate branch name, commit message, PR title, and PR body aligned to project preferences.*

- [ ] Read `.pr-pilot/preferences.md`. Resolve missing keys via fallback chain (see `references/preferences.md`).
- [ ] Run conflict detection: compare preferences against actual repo conventions. If contradiction found (e.g. `提交语言: 英文` but all recent commits are Chinese) → stop and ask user before proceeding.

**Generate branch name** (following `分支格式` pattern):
- [ ] Compose branch name using the pattern: substitute `<short-desc>` with concise English hyphenated description (e.g. `feat/add-login-flow`)
- [ ] Verify branch doesn't exist: `git show-ref --verify --quiet "refs/heads/<branch>"` → if exists, ask user or add disambiguator

**Generate commit message** (following `提交格式` + `提交语言`):
- [ ] Describe changes objectively — every file, every functional change. No speculation.
- [ ] Follow the configured format (default: Conventional Commits). Match repo's existing type/scope conventions.
- [ ] Write to file: `.pr-pilot/temp/commit-msg.txt` (via Write tool)

**Generate PR title and body** (following `PR格式` + `PR语言`):
- [ ] Title: concise summary of the change
- [ ] Body: represent **every** change (files added/modified/deleted, functional changes). Model after existing repo PRs.
- [ ] If `PR模板路径` exists → read and fill that template.
- [ ] Write to files: `.pr-pilot/temp/pr-title.txt`, `.pr-pilot/temp/pr-body.txt` (via Write tool)

### Step 5 — 一键创建 (One-Click Create PR)

*Purpose: Script runs all mechanical git/gh operations with one call.*

- [ ] Pick wt-name: `printf '%04x-%04x\n' $RANDOM $RANDOM`
- [ ] Pick wt-path: `<repo-root>/.pr-pilot/worktrees/<wt-name>`
- [ ] Mark `一键创建` → `进行中` (conceptual — no task doc in this skill; track via state files)
- [ ] Run pilot.sh:
  ```bash
  bash <skill-dir>/scripts/pilot.sh \
    ".pr-pilot" \
    "<base>" \
    "<new-branch>" \
    "<wt-name>" \
    "<wt-path>" \
    "@.pr-pilot/temp/commit-msg.txt" \
    "@.pr-pilot/temp/pr-title.txt" \
    "@.pr-pilot/temp/pr-body.txt" \
    <file1> <file2> ...
  ```
- [ ] If `pilot.sh` exits 0 → proceed to Step 6
- [ ] If exits non-zero → read stderr to identify failed step:
  - **FAIL: tool_check** → install missing tool, retry
  - **FAIL: create_worktree** → branch exists or path conflict. Fix and retry
  - **FAIL: copy_files** → file not found. Verify scope paths, retry
  - **FAIL: commit** → commit failed. Check commit message, retry
  - **FAIL: push** → network/auth. Retry with `https` manually or `ssh`, see worktree-pr's `wtpush` for patterns
  - **FAIL: create_pr** → `gh` error. Check auth, retry
  - After fixing cause, re-run same `pilot.sh` command — it resumes from the failed step

### Step 6 — 完成提示 (Finish & Prompt)

- [ ] On success, `pilot.sh` prints the PR URL. Capture it.
- [ ] Tell user:
  > "PR created: <URL>
  > Branch `<new-branch>` has been pushed. The worktree is at `<wt-path>`.
  > Please wait for CI to finish before merging. Use `gh pr checks <URL>` to monitor status."
- [ ] Do NOT wait for CI or run any CI-checking tool. The skill stops here.
- [ ] Ask user: "Would you like me to clean up the worktree (remove `<wt-path>`), or keep it for now?"
- [ ] If cleanup requested: `rm -rf <wt-path>`

## Temp File Conventions

Always use `.pr-pilot/temp/` for temp files (commit messages, PR bodies). It is
repo-local to avoid cross-drive issues on Windows, and gitignored.

```bash
# Use via pilot.sh's @path convention:
bash <skill-dir>/scripts/pilot.sh ".pr-pilot" "main" "feat/foo" "a1b2" ".pr-pilot/worktrees/a1b2" \
  "@.pr-pilot/temp/commit-msg.txt" \
  "@.pr-pilot/temp/pr-title.txt" \
  "@.pr-pilot/temp/pr-body.txt" \
  "src/file1.ts" "src/file2.ts"
```

## Conventions & Error Handling

- Run scripts, don't pre-mark success. Read real output.
- Be honest: report failures with actual stderr.
- `pilot.sh` resume: re-run same command, it skips completed steps via state markers.
- Any unexpected failure: report (a) which step failed (b) error message (c) the command to retry.
- This skill works with both committed and uncommitted changes. For entirely uncommitted work, `worktree-pr` may be a better fit.
- Concurrency is the user's responsibility — the skill takes no locks.
