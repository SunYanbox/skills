---
name: worktree-pr
description: >-
  Isolate uncommitted changes into a PR via a throwaway git worktree. Use when:
  (1) "make a PR for these changes", (2) "commit and push src/core",
  (3) "isolate these changes into a PR", (4) "create a PR without touching my
  branch", (5) "put these edits in their own worktree", or (6) resume a paused
  worktree-PR task. Prefer this over hand-rolled git worktree + gh pr sequences.
---

# worktree-pr

Turn a subset of **uncommitted changes** into a clean pull request using a
throwaway git worktree, then commit, push, open the PR, and watch CI to green.

Mental model: user is on branch `start` with uncommitted edits. This skill spins
up a new worktree on a fresh branch from `start`, **copies** the relevant files
into it, commits there, pushes, and opens a PR back to `start`. The user's
original working tree is left untouched.

State persists under `.wt-pr/` in the repo root; tasks survive interruption.

## Tool Usage Policy (能力覆盖)

Decide tool choice by **capability coverage**, not blanket prohibitions:

| Operation type | Tool | Rule |
|---|---|---|
| Side effects (git/gh, complex ops) | `scripts/` bundled scripts via **Bash** | When `scripts/` has a script for the task, **must** use it. Never hand-roll equivalent command chains. |
| Status updates & non-script reads/writes | **Edit** / **Read** tools | Edit task doc, read files → use native tools directly. See `references/status-schema.md`. |
| Pure file I/O (`cat`, `sed`, `grep`, `awk` on files) | **Read** / **Edit** / **Grep** tools | **Forbidden** via Bash when a native tool can do the job. |
| Git status queries (`diff`, `status`, `log`) | **Bash** (allowed) | No native tool equivalent exists; Bash is the right choice. |

## Bundled Scripts

`<skill-dir>` = absolute path of the directory containing this `SKILL.md`.
All scripts print ASCII English to stdout, aimed at the Agent. Success → exit 0;
failure → non-zero + a short reason on stderr.

| Script | Args | What it does |
|---|---|---|
| `ghchk` | (none) | Exits 0 if `git` and `gh` are on PATH, else 1. |
| `wtinit` | `<start-branch> <wt-name> <wt-path> <user-request>` | Creates `.wt-pr/` layout + initial task doc. Idempotent on dirs; always rewrites the doc. |
| `wtadd` | `<start-branch> <new-branch> <wt-path>` | `git worktree add -b <new> <path> <start>`. Caller supplies the branch name. |
| `wcp` | `<wt-path> <file1> [file2 …]` | Diff-copies files/dirs into the worktree. ≤100 MB → hash compare; >100 MB → mtime. |
| `wtcmt` | `<wt-path> <message> [<start-branch>]` | `git add -A && git commit` in the worktree. Optional `<start-branch>` enables idempotency: if nothing staged but a commit already exists on top of start-branch → `ALREADY_COMMITTED` exit 0. `@path` reads message from file. |
| `wtpush` | `<wt-path> <mode>` | Push to origin. `mode` = `https` or `ssh`. 3 internal retries. |
| `wtpr` | `<wt-path> <base> <title> <body>` | `gh pr create --base <base>`. `@path` reads title/body from file. Prints PR URL. |
| `wtciwait` | `<PR_URL>` | Polls CI at 5s→30s→90s→5m→10m. Prints `PASSED`/`NO_CHECKS`/`MERGED` (exit 0), `FAILED:`/`TIMEOUT:`/`PR_CLOSED`/`ERROR:` (exit 1). **Run in background.** |

## State Files (`.wt-pr/`)

```
.wt-pr/
├── .gitignore       # contents: *
├── commit.md        # commit & PR preferences (see references/preferences.md)
├── activate/        # in-progress task docs: <start-branch>-<wt-name>.md
├── done/            # archived task docs
└── temp/            # Agent temp files (commit messages, PR bodies)
```

For the **task document schema**, **status values**, and **status update rules**,
see [`references/status-schema.md`](references/status-schema.md).

For **commit.md schema** and **preference resolution**, see
[`references/preferences.md`](references/preferences.md).

## The Workflow

Run steps in order. Update the task doc after every step (Edit tool + Read verify).

### Step 0 — Initialize & resume check

- [ ] If `.wt-pr/` missing: `bash <skill-dir>/scripts/wtinit placeholder placeholder placeholder placeholder`
- [ ] Determine current branch: `git rev-parse --abbrev-ref HEAD`
- [ ] Scan `.wt-pr/activate/` for docs starting with `<current-branch>-`

**Resume logic**: find the first step not marked `[完成]`. Re-run that step's
script — scripts with idempotency checks (`wtcmt`) will safely skip already-done
work. Update the doc to reflect reality before proceeding.

If no in-progress doc exists and user didn't specify a file scope → ask which
files to include before proceeding to Step 1.

### Step 1 — Tool check

- [ ] `bash <skill-dir>/scripts/ghchk`
- [ ] Non-zero → stop, tell user which tool is missing

### Step 2 — Name the branch, create the worktree

- [ ] Resolve branch style from repo's existing branches. Record in `commit.md` under `分支格式`
- [ ] Generate branch name from `分支格式` + user's change description
- [ ] Generate wt-name: `printf '%04x-%04x\n' $RANDOM $RANDOM`
- [ ] Pick wt-path: `<repo-root>/.wt-pr/worktrees/<wt-name>`
- [ ] `bash <skill-dir>/scripts/wtinit "<start>" "<wt-name>" "<wt-path>" "<user-request>"`
- [ ] Mark `检查工具` → `完成`, `创建工作树` → `进行中`
- [ ] `bash <skill-dir>/scripts/wtadd "<start>" "<new-branch>" "<wt-path>"`
- [ ] Mark `创建工作树` → `完成`

### Step 3 — Resolve scope & copy files

- [ ] Map user's scope to concrete file/dir paths (relative to repo root). Ask if unsure.
- [ ] Mark `复制文件` → `进行中`
- [ ] `bash <skill-dir>/scripts/wcp "<wt-path>" "path/one" "dir/two" …`
- [ ] Optionally verify: `git -C "<wt-path>" status --short`
- [ ] Mark `复制文件` → `完成`

### Step 4 — Generate commit message & commit

- [ ] Capture full diff: `git -C "<wt-path>" diff <start-branch>...HEAD`
- [ ] Describe changes objectively — every file, every functional change. No speculation.
- [ ] Read `.wt-pr/commit.md` for preferences. Resolve missing keys via fallback chain (see `references/preferences.md`). Run conflict detection — **if a contradiction is found, stop and ask the user before proceeding**.
- [ ] Produce Conventional Commits message in configured language
- [ ] Mark `提交` → `进行中`
- [ ] `bash <skill-dir>/scripts/wtcmt "<wt-path>" "<message>" "<start-branch>"`
  - `ALREADY_COMMITTED` → step already done; proceed
- [ ] If message is awkward to quote → write to `.wt-pr/temp/` file, pass `@<path>`
- [ ] Mark `提交` → `完成`

### Step 5 — Push to remote

- [ ] `bash <skill-dir>/scripts/wtpush "<wt-path>" https`
- [ ] If fails → `bash <skill-dir>/scripts/wtpush "<wt-path>" ssh`
- [ ] Both fail → mark `推送` → `失败`, report error + doc path, hand control to user
- [ ] Mark `推送` → `完成`

### Step 6 — Create the pull request

- [ ] Base = `<start-branch>` (or user-specified target)
- [ ] Capture full diff + commit list: `git -C "<wt-path>" diff <start>...HEAD` and `git log <start>..HEAD --oneline`
- [ ] Describe changes objectively — represent **every** change in the PR
- [ ] Read `.wt-pr/commit.md` PR preferences. Run conflict detection on `PR语言`/`PR格式` — **if a contradiction is found, stop and ask the user before proceeding**.
- [ ] Mark `创建PR` → `进行中`
- [ ] `bash <skill-dir>/scripts/wtpr "<wt-path>" "<base>" "<title>" "<body>"`
- [ ] Capture PR URL. Mark `创建PR` → `完成`

### Step 7 — Wait for CI & fix failures

- [ ] Mark `CI等待与修复` → `进行中`
- [ ] `bash <skill-dir>/scripts/wtciwait "<PR_URL>"` (**run in background**)

When background task completes, read stdout:

| Output | Action |
|--------|--------|
| `PASSED` / `NO_CHECKS` / `MERGED` | CI green → Step 8 |
| `FAILED:`/`TIMEOUT:` | Fix loop below |
| `PR_CLOSED` | Report to user; stop |
| `ERROR:` | `gh` itself failed (auth/network). Fix cause, re-run once. If persists → mark `失败`, report |

**Fix loop** (max 3 rounds):

1. Inspect failing checks: `gh pr checks "<PR_URL>"`, `gh run view <id> --log-failed`
2. Make targeted fix **in the worktree** (not user's main tree)
3. Re-commit (`wtcmt "<wt-path>" "<message>" "<start-branch>"`) — pass `<start-branch>` for idempotency (ALREADY_COMMITTED if nothing new staged) — and re-push (`wtpush`)
4. Increment `修复失败计数` in task doc (Edit: `N` → `N+1`; Read to verify)
5. Re-run `wtciwait` in background

After 3rd push with CI still not green → mark `CI等待与修复` → `失败`, report, hand control to user.

### Step 8 — Finish & archive

Only on full success (all steps completed, CI green / NO_CHECKS / MERGED):

- [ ] Move doc: `.wt-pr/activate/<name>.md` → `.wt-pr/done/<name>.md`
- [ ] In moved doc: `清理标志` → `已存档`, `CI等待与修复` → `完成`
- [ ] Tell user the PR URL + task archived

Otherwise leave doc in `activate/` for resumption. Worktree removal is optional:
`git worktree remove --force "<wt-path>"`.

## Temp File Conventions

Always use `.wt-pr/temp/` for temp files (commit messages, PR bodies). It is
repo-local (avoids cross-drive issues on Windows), created by `wtinit`,
and gitignored.

```bash
MSGFILE=".wt-pr/temp/commit-$(printf '%04x' $RANDOM).txt"
# Write to MSGFILE via Write tool, then:
bash <skill-dir>/scripts/wtcmt "<wt-path>" "@$MSGFILE"
```

## Conventions & Error Handling

- Run script first, update doc from real output. Never pre-mark a step complete.
- Be honest about outcomes: report failures with stderr, timeouts as timeouts.
- Push retry: `wtpush https` (3) → `wtpush ssh` (3) → stop & report.
- CI fix limit: 3 rounds. Over limit or TIMEOUT → stop & report.
- Any unexpected failure: mark step `失败`, report (a) step (b) error (c) doc path.
- This skill isolates *uncommitted* edits. Already-committed changes won't appear → tell user, ask how to proceed.
