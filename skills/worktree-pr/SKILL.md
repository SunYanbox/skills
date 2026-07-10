---
name: worktree-pr
description: >-
  Isolate a set of local, uncommitted changes into their own pull request using a
  throwaway git worktree, then commit, push, open the PR, and babysit CI until it
  goes green. Use this skill whenever the user wants to turn some changes into a PR
  without disturbing their current working tree or branch — signals include "make a PR
  for these changes", "commit and push src/core", "isolate these changes into a PR",
  "create a PR without touching my branch", "put these edits in their own worktree", or
  any request to ship a subset of uncommitted edits as a pull request. Also use it when
  the user references the worktree-pr workflow, the .wt-pr cache, or asks to resume a
  paused worktree-PR task. Prefer this skill over hand-rolled git worktree + gh pr
  sequences — its bundled scripts and persistent task docs make the flow resumable and
  token-cheap.
---

# worktree-pr

Turn a subset of a repo's **uncommitted changes** into a clean pull request using a
throwaway git worktree, then commit, push, open the PR, and watch CI to green.

The mental model: the user is on branch `start` (e.g. `main`) with a pile of uncommitted
edits. This skill spins up a new worktree on a fresh branch cut from `start`, **copies**
(not moves) the relevant changed files into it, commits there, pushes, and opens a PR back
to `start`. The user's original working tree is left exactly as it was.

State is persisted under `.wt-pr/` in the repo root, so a task survives interruption and
can be resumed.

## How to use the bundled scripts

Every mechanical step is a short bash script in `<skill-dir>/scripts/`. **Always use the
scripts** — never hand-roll the equivalent git/gh chains. They are the cheap,
deterministic interface the skill is built around.

- `<skill-dir>` is the absolute path of the directory containing this `SKILL.md`.
  Substitute it everywhere below (e.g. `bash /abs/path/scripts/ghchk`). When the repo is
  the skills repo itself and you are at its root, `skills/worktree-pr/scripts/...` works.
- All scripts print ASCII English to stdout, aimed at you (the Agent), with no decorative
  filler. Success → exit 0; failure → non-zero exit + a short reason on stdout/stderr.
- Run them through the Bash tool. A few take paths with spaces — keep the path as a single
  quoted argument and the scripts handle it.

### Script reference

| Script | Args | What it does |
|---|---|---|
| `ghchk` | (none) | Exits 0 if `git` and `gh` are on PATH, else 1. |
| `wtinit` | `<start-branch> <wt-name> <wt-path> <user-request>` | Creates `.wt-pr/` + `.gitignore`, and the initial task doc in `activate/`. Idempotent on directories; always (re)writes the task doc. Call for each new task, even if `.wt-pr/` already exists. |
| `wtadd` | `<start-branch> <new-branch> <wt-path>` | `git worktree add -b <new-branch> <wt-path> <start-branch>`. The caller supplies the full new branch name; the script does not derive or infer it. |
| `wcp` | `<wt-path> <file1> [file2 ...]` | Diff-copies the listed files/dirs from the current working tree into `<wt-path>`. ≤100 MB → git-hash compare; >100 MB → mtime compare. Skips identical files. |
| `wtcmt` | `<wt-path> <message>` | In the worktree: `git add .` then `git commit`. Message may be multi-line. Prefix the message with `@` to instead read it from a file: `@path/to/msg.txt`. |
| `wtpush` | `<wt-path> <mode>` | Push the worktree's branch to origin. `mode` = `https` or `ssh` (ssh temporarily swaps origin to an SSH URL, then restores it). 3 internal retries per call. |
| `wtpr` | `<wt-path> <base-branch> <title> <body>` | `gh pr create --base <base>`. Title/body may be multi-line. Prefix either with `@` to read from a file. Prints the new PR URL. |
| `wtciwait` | <PR_URL> | Polls CI at 5s, 30s, 90s, 5m, 10m. Prints `PASSED` (exit 0), `FAILED: <names>` (exit 1), `NO_CHECKS` (exit 0, no CI configured), `TIMEOUT: <names>` (exit 1), or `ERROR: <reason>` (exit 1 — `gh` itself failed, e.g. auth/network; do **not** treat as passed). **Run in the background.** |
| `wtstep` | `<doc> [step] [status]` · `<doc> counter <set\|inc\|dec> [n]` | Reads (`<doc>` alone) or updates a step status / the failure counter in the task doc. Validates step + status; rejects unknown values so the markers can't silently drift. Use this instead of hand-editing the markers. |

## The state files (`.wt-pr/`)

Run `wtinit` once to create the layout. It ignores itself with `.gitignore` (`*`).

```
.wt-pr/
├── .gitignore          # contents: *  (ignores everything under .wt-pr/)
├── commit.md           # commit & PR preferences — maintained by both user and Agent
├── activate/           # in-progress task docs:  <start-branch>-<wt-name>.md
├── done/               # archived task docs (only after full clean success)
└── temp/               # Agent temp files (commit messages, PR bodies, etc.)
```

### Task document

`wtinit` writes the initial task doc at `.wt-pr/activate/<start-branch>-<wt-name>.md` in
UTF-8 with all step statuses `[待办]`. **After every step, update this doc with `wtstep`**
(not a free-form edit) — it validates the step name and status, so the markers can't silently
drift from reality and the resume logic in Step 0 stays trustworthy. Set a step's status
(`待办` → `进行中` → `完成`, or `失败` on error) with `wtstep <doc> <step> <status>`, and bump
the failure counter with `wtstep <doc> counter inc` after each CI fix round is pushed. The
exact schema (keep these keys and values):

```markdown
- 起始分支: <branch>
- 工作树名: <wt-name>
- 工作树路径: <absolute path>
- 用户要求: <user's original request, verbatim>
- 步骤状态:
  - 检查工具: [待办]
  - 创建工作树: [待办]
  - 复制文件: [待办]
  - 提交: [待办]
  - 推送: [待办]
  - 创建PR: [待办]
  - CI等待与修复: [待办]
- 修复失败计数: 0
- 清理标志: 暂不清理
```

Status values: `待办` (pending) · `进行中` (in progress) · `完成` (done) · `失败` (failed).
清理标志 values: `暂不清理` (no cleanup) · `待清理` (to clean) · `已清理` (cleaned) · `已存档` (archived).
清理标志 is a plain line the agent edits directly; the step statuses and `修复失败计数` go through `wtstep`:

```bash
# read all step statuses + the counter
DOC=.wt-pr/activate/<start-branch>-<wt-name>.md
bash <skill-dir>/scripts/wtstep "$DOC"
# mark a step done
bash <skill-dir>/scripts/wtstep "$DOC" 推送 完成
# bump the CI-fix-failure counter after a fix round
bash <skill-dir>/scripts/wtstep "$DOC" counter inc
```

### Preferences file `commit.md`

This file is **maintained by both the user and the Agent** in UTF-8.

- **Who creates it:** the Agent creates it at Step 2 / Step 4 if it does not yet exist.
- **Who updates it:** either party at any time. The Agent will update it when it infers a
  missing required key from the project (see fallback chain below) or when the user
  explicitly asks to change a preference. The user may also edit it directly.
- **When the Agent updates it:** (1) when a required key is missing and the Agent resolves it
  via the fallback chain, the Agent writes the resolved value back; (2) when the user
  requests a change to an existing preference.

Required keys (one per line):

- `分支格式`: branch name pattern(s), comma-separated, e.g. `feat/<ticket>-<short-desc>, fix/<short-desc>`
- `提交语言`: `中文` or `英文`
- `PR语言`: `中文` or `英文`

Optional keys: `提交格式`, `提交模板路径`, `PR格式`, `PR模板路径`, plus any free-form prose
preferences appended on their own lines.

If `commit.md` is missing or lacks a required key, fall back in order: (1) project config
files (`.commitlintrc*`, `cz-config.js`, `.github/COMMIT_TEMPLATE.md`, PR templates under
`.github/`), (2) the naming/style of existing branches and merged PRs in the repo, (3) ask
the user. Write what you settled on back into `commit.md` so later runs don't re-ask.

#### Conflict detection

When the Agent discovers that a value in `commit.md` **contradicts** observable reality
in the repo, it must **stop and ask the user immediately** — do not silently follow
`commit.md` and do not silently ignore it. The user's answer determines the correct
behavior, and the Agent must update `commit.md` accordingly.

Examples of contradictions the Agent should detect:

- `提交语言: 英文` but existing commit messages are consistently in Chinese (or vice
  versa).
- `分支格式: feat/<short-desc>` but the repo's actual branch names consistently follow
  a different pattern like `feature/<ticket>-<desc>`.
- `PR语言: 中文` but all existing PRs in the repo use English titles and bodies.

On detection, ask a concrete question:

> `commit.md` says `提交语言: 英文`, but I see that all recent commits in this repo
> use Chinese messages. Which should I follow?

Then update `commit.md` with the user's answer to keep future runs consistent.

## The workflow

Run the steps in order. Never skip the per-step task-doc update — it is what makes a
paused task resumable.

### Step 0 — Initialize & look for an in-progress task

1. If `.wt-pr/` does not exist, run `wtinit` with placeholder args to create the
   directory skeleton (it is idempotent on directories):
   ```bash
   bash <skill-dir>/scripts/wtinit "placeholder" "placeholder" "placeholder" "placeholder"
   ```
   Step 2 will call `wtinit` again with the real values — it overwrites the placeholder
   task doc but leaves the directories and `.gitignore` alone.
2. Determine the current branch: `git rev-parse --abbrev-ref HEAD`.
3. Scan `.wt-pr/activate/` for any doc whose name starts with `<current-branch>-`.
   Apply the following logic based on the user's request:

   **A. User did NOT specify a file scope** (e.g. "make a PR for my changes"):
   - If exactly one in-progress doc exists → ask: "Found an in-progress task
     (`<name>`). Continue it, or start a new one?" If continue → resume from the first
     `待办`/`进行中`/`失败` step. If new → proceed to Step 1.
   - If multiple in-progress docs exist → list them and ask the user which one to
     continue. The user controls concurrency — the Agent must not operate on two
     worktrees simultaneously without the user's explicit choice.
   - If none → stop and tell the user: no in-progress task found and no file scope
     specified. Ask which files to include in the PR before proceeding to Step 1.

   **B. User specified a clear file scope** (e.g. "commit and push src/core"):
   - If one in-progress doc's change scope **exactly matches** the user's scope → ask:
     "Found an in-progress task (`<name>`) with the same file scope. Continue it?"
     If yes → resume; if no → proceed to Step 1 to start a new task.
   - If no in-progress doc matches the scope → proceed directly to Step 1 (start a new
     task without asking).
   - If multiple docs partially overlap → treat as no exact match and proceed to Step 1.

### Step 1 — Tool check

```bash
bash <skill-dir>/scripts/ghchk
```

Non-zero exit → stop and tell the user which tool (`git` / `gh`) is missing.

### Step 2 — Name the branch, create the worktree

1. **Resolve the branch style.** Look at the repo's branch names (`git branch -a` and
   `git for-each-ref --format='%(refname:short)' refs/heads refs/remotes`). Extract the
   structure: prefix (`feat`/`fix`/…), separator (`/`, `-`), whether a ticket number is
   present, language of the descriptor, etc. If the styles are consistent, adopt that
   style. If they clash, ask the user which they prefer. Record the result in `commit.md`
   under `分支格式` (build the file now if it's missing — you'll fill the other keys at
   Step 4, but capture `分支格式` now).
2. **Generate the new branch name.** Based on the `分支格式` pattern and the nature of the
   user's changes, compose a complete branch name yourself (e.g. `feat/add-login-flow`,
   `fix/null-ptr-crash`). Use the pattern as a template: substitute `<short-desc>` with a
   concise English hyphenated description of the change, omit or fill `<ticket>` if
   applicable.
3. **Generate the worktree name.** Run `printf '%04x-%04x\n' $RANDOM $RANDOM` (e.g.
   `7f3a-9c21`) and use the output as `<wt-name>`. Don't invent a string yourself — `$RANDOM`
   avoids collisions and bias.
4. **Pick the worktree path.** Default: `<repo-root>/.wt-pr/worktrees/<wt-name>` (relative
   form `.wt-pr/worktrees/<wt-name>` works when you're at the repo root). This subdir is
   gitignored, so it never shows up in `git status`.
5. Write the initial task doc:
   ```bash
   bash <skill-dir>/scripts/wtinit "<start-branch>" "<wt-name>" "<wt-path>" "<user-request verbatim>"
   ```
   (`<start-branch>` is the current branch.) Then mark `检查工具` → `完成`,
   `创建工作树` → `进行中` in the task doc.
6. Create the worktree:
   ```bash
   bash <skill-dir>/scripts/wtadd "<start-branch>" "<new-branch>" "<wt-path>"
   ```
   On success, set `创建工作树` → `完成`.

> The worktree is checked out clean from `<start-branch>`'s tip. Your job in Step 3 is to
> overlay the user's uncommitted edits onto it.

### Step 3 — Resolve the change scope and copy files

1. Understand the user's natural-language scope (e.g. "the changes under `src/core`", "the
   two files I just edited"). Map it to a concrete list of files/directories **relative to
   the repo root**. If you cannot resolve it confidently, **ask the user** — do not guess.
2. Set `复制文件` → `进行中`, then:
   ```bash
   bash <skill-dir>/scripts/wcp "<wt-path>" "path/one" "dir/two" ...
   ```
   `wcp` only copies files that actually differ (hash for ≤100 MB, mtime for >100 MB), so
   you can pass whole directories without worrying about redundant work. Quote any path with
   spaces as one argument.
3. After it returns, optionally verify with `git -C "<wt-path>" status --short`; then set
   `复制文件` → `完成`.

### Step 4 — Generate the commit message and commit

1. See what's staged in the worktree: `git -C "<wt-path>" diff --staged` (and `git -C
   "<wt-path>" diff` if nothing is staged yet — `wtcmt` will `git add .` first anyway).
2. **Capture the full diff.** Before composing the message, examine the complete set of
   changes via `git -C "<wt-path>" diff <start-branch>...HEAD` (all changes since
   branching). The commit message must objectively represent **every** change visible in
   the diff — every file added/modified/deleted, every functional change, every rename.
   Do not cherry-pick a subset of the changes; do not omit files or changes just because
   they seem minor. A commit message that omits changes is misleading.
3. **Describe the changes objectively** — what was added/changed/removed, in what area.
   Do not speculate about intent, motivation, or the future. Keep it factual.
4. Read `.wt-pr/commit.md` for the commit preferences. Resolve any missing required key
   (`提交语言` especially) via the fallback chain (project config → existing commits →
   ask user). Write resolved values back into `commit.md`. **Conflict detection:** if
   a value in `commit.md` contradicts the repo's actual commit history (e.g.
   `提交语言: 英文` but recent commits are in Chinese), follow the
   [conflict detection](#conflict-detection) procedure — stop and ask the user, then
   update `commit.md` with their answer.
5. Produce a **Conventional Commits** message in the configured language, e.g.
   `refactor(core): delete old parser, adjust new parser signature`. Match the repo's
   existing commit style for type/scope conventions.
6. Set `提交` → `进行中`, then commit:
   ```bash
   bash <skill-dir>/scripts/wtcmt "<wt-path>" "<conventional commit message"
   ```
   For a multi-line message (subject + body) pass it as one quoted argument with embedded
   newlines. If the message contains single quotes or is otherwise awkward to quote, write
   it to a file under `.wt-pr/temp/` and pass `@<path>` instead (see
   [Temporary file conventions](#temporary-file-conventions)). On success, `提交` → `完成`.

### Step 5 — Push to remote

```bash
bash <skill-dir>/scripts/wtpush "<wt-path>" https
```

`wtpush https` retries up to 3 times internally. If its exit code is non-zero, fall back to
SSH (it temporarily rewrites origin to an SSH URL and restores it after):

```bash
bash <skill-dir>/scripts/wtpush "<wt-path>" ssh
```

If SSH also fails (after its own 3 retries), **stop**: set `推送` → `失败`, print the error
and the task-doc path, and hand control to the user. On success, `推送` → `完成` and capture
the remote branch name the script reports.

### Step 6 — Create the pull request

1. The PR **base** is `<start-branch>` (the branch the user was on), unless the user named a
   different target.
2. **Base PR content on the full branch diff.** Examine all changes since branch creation:
   ```bash
   git -C "<wt-path>" diff <start-branch>...HEAD
   ```
   Also review the full commit list: `git -C "<wt-path>" log <start-branch>..HEAD --oneline`.
   The PR title and body must represent **every** change in this diff — every file added,
   modified, or deleted, every functional change. Do not write a PR that only covers the
   most recent commit or a subset of changes. A PR that omits changes is misleading; it
   represents the full branch.
3. **Describe the changes objectively** — what was added/changed/removed, in what area.
   Do not speculate about intent, motivation, or the future. Keep it factual.
4. Read `.wt-pr/commit.md` PR preferences. **Conflict detection:** if `PR语言`
   or `PR格式` in `commit.md` contradicts the repo's existing PR style (check with
   `gh pr list --state all --limit 10`), follow the
   [conflict detection](#conflict-detection) procedure — stop and ask the user.
   If `PR模板路径` exists, read that template and
   fill it. Otherwise model the title/body on the repo's existing open or merged PRs (use
   `gh pr list --state all --limit 10` and `gh pr view <num>`). Generate title + body in the
   configured `PR语言`.
5. Set `创建PR` → `进行中`, then:
   ```bash
   bash <skill-dir>/scripts/wtpr "<wt-path>" "<base-branch>" "<title>" "<body>"
   ```
   `wtpr` prints the new PR URL. Capture it. For long or quote-heavy bodies, write the body
   to a file under `.wt-pr/temp/` and pass `@<path>` as the body arg (see
   [Temporary file conventions](#temporary-file-conventions)). Set `创建PR` → `完成`.

### Step 7 — Wait for CI and fix failures

`wtciwait` polls for up to ~10 minutes and is a long-running call — **run it in the
background** so it isn't bound by the interactive Bash timeout, and you'll be re-invoked
when it exits:

```bash
# invoke via the Bash tool with run_in_background: true
bash <skill-dir>/scripts/wtciwait "<PR_URL>"
```

Set `CI等待与修复` → `进行中` before launching. When the background task finishes, read its
stdout:

- `PASSED` → CI is green. Skip to Step 8.
- `NO_CHECKS` → no CI is configured for this repo. Treat as success. Skip to Step 8.
- `ERROR: <reason>` → `gh` itself failed (auth, network, PR not found). This is **not** a check failure and **not** a pass — do **not** enter the fix loop as if code were broken. Set `CI等待与修复` → `进行中` stays, re-run `wtciwait` once after fixing the cause (e.g. `gh auth login`, network). If it keeps erroring, set `CI等待与修复` → `失败`, report the reason + task-doc path, and hand control to the user.
- `FAILED: <names>` or `TIMEOUT: <names>` → some checks didn't pass. Go into the fix loop:
  1. Inspect the failing checks: `gh pr checks "<PR_URL>"` and, for log detail,
     `gh run view <run-id> --log-failed` (or reuse the `gh-actions-debug` skill for a fast
     root-cause). Find the concrete failure. Use the `codegraph` tools to locate the code.
  2. Make a targeted fix **in the worktree** (`<wt-path>`), not the user's main tree.
  3. Re-commit (`wtcmt`) and re-push (`wtpush <wt-path> https` with ssh fallback as needed).
  4. **Increment `修复失败计数`** in the task doc:
     ```bash
     bash <skill-dir>/scripts/wtstep <doc> counter inc
     ```
  5. Re-run `wtciwait` in the background. Repeat.

  **Hard limit: 3 fix rounds.** If after the 3rd push CI still isn't green, **stop**: set
  `CI等待与修复` → `失败`, report the un-passing checks, and hand control to the user.
  Likewise, a `TIMEOUT` (checks still pending after 10 min) means stop and report — don't
  spin forever.

### Step 8 — Finish & archive

Only when the **full flow succeeded with zero errors and all CI checks pass** (or
`NO_CHECKS`):

1. Move the task doc: `.wt-pr/activate/<name>.md` → `.wt-pr/done/<name>.md`.
2. In the moved doc, set `清理标志` → `已存档` and `CI等待与修复` → `完成`.
3. Tell the user the PR URL and that the task is archived.

In every other situation (a step failed, CI not green, hits a retry limit, or the user
paused), **leave the doc in `activate/`** so it can be resumed. You may set `清理标志` →
`待清理`. Concurrency is the user's responsibility — the skill takes no locks.

The throwaway worktree itself is left in place across the run (later steps operate in it).
Removing it is optional cleanup the user can request afterward; if asked, run
`git worktree remove --force "<wt-path>"`.

## Temporary file conventions

The Agent often needs to write a commit message or PR body to a temp file before
passing it to `wtcmt` or `wtpr` via the `@path` syntax. **Always use
`.wt-pr/temp/`** as the temp directory — it is created by `wtinit`, is gitignored
by the `.wt-pr/.gitignore`, and is repo-local.

### Why not system temp (`$TMPDIR`, `%TEMP%`, `/tmp`)?

On Windows the system temp directory (`C:\Users\…\AppData\Local\Temp`) may be on
a **different drive** from the repo (`E:\…`). Git worktree paths and `@`-file
references must be reachable from the worktree's working directory; cross-drive
paths can confuse tools or require different quoting. A repo-local temp dir
avoids this entirely and keeps cleanup trivial (just delete the file after use).

### Usage pattern

```bash
# Write the commit message to a temp file
MSGFILE=".wt-pr/temp/commit-$(printf '%04x' $RANDOM).txt"
cat > "$MSGFILE" <<'EOF'
feat(scope): add new feature

Detailed body here.
EOF

# Commit using the temp file
bash <skill-dir>/scripts/wtcmt "<wt-path>" "@$MSGFILE"

# Clean up when done (optional — the whole temp/ dir is gitignored)
rm -f "$MSGFILE"
```

The same pattern applies to PR bodies with `wtpr`.

## Conventions & error handling

- **Always run a script, then update the task doc from its real output.** Don't pre-mark a
  step complete.
- **Be honest about outcomes:** if a script failed, say so with its stderr; if CI timed
  out, say timeout; only report success when `git`/`gh`/CI actually confirm it.
- **Push retry ladder:** `wtpush https` (3) → `wtpush ssh` (3) → stop & report.
- **CI fix limit:** 3 rounds (each = edit in worktree + commit + push + re-wait). Over the
  limit, or a `TIMEOUT`, means stop & report.
- **Any unexpected failure** at any step: set that step's status to `失败`, and tell the
  user (a) the step, (b) the error, (c) the path to the task doc so they can resume or
  decide.
- **Scope of changes:** this skill isolates *uncommitted* edits. If the user's changes are
  already committed to the start branch, copying won't surface them — tell the user and ask
  how to proceed rather than opening an empty PR.
