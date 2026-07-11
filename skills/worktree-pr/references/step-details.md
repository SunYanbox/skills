# Step-by-Step Procedural Details

This file holds detailed procedural guidance for each workflow step. The
SKILL.md checklist items summarize **what** to do; this file explains **how**.

---

## `<skill-dir>` Substitution

`<skill-dir>` is the absolute path of the directory containing `SKILL.md`.
Substitute it everywhere (e.g. `bash /abs/path/scripts/ghchk`). When the repo
is the skills repo itself and you are at its root, `skills/worktree-pr/scripts/...`
also works. Run all scripts through the Bash tool. A few scripts accept paths
with spaces — keep the path as a single quoted argument and the scripts handle
it.

---

## Step 2 — Branch Style Resolution & Name Generation

### How to resolve branch style

Run these commands to inspect the repo's branch names:

```bash
git branch -a
git for-each-ref --format='%(refname:short)' refs/heads refs/remotes
```

Extract the structure: prefix (`feat`/`fix`/…), separator (`/`, `-`), whether a
ticket number is present, language of the descriptor, etc. If the styles are
consistent, adopt that style. If they clash, ask the user which they prefer.

Record the result in `commit.md` under `分支格式` (build the file now if it's
missing — you'll fill the other keys at Step 4, but capture `分支格式` now).

### How to generate the branch name

Based on the `分支格式` pattern and the nature of the user's changes, compose a
complete branch name yourself (e.g. `feat/add-login-flow`, `fix/null-ptr-crash`).
Use the pattern as a template: substitute `<short-desc>` with a concise English
hyphenated description of the change, omit or fill `<ticket>` if applicable.

---

## Step 3 — Scope-Mapping Examples

Understand the user's natural-language scope and map it to a concrete list of
files/directories **relative to the repo root**. Examples:

| User says | Map to |
|-----------|--------|
| "the changes under `src/core`" | `src/core` (directory) |
| "the two files I just edited" | Ask: "Which two files?" |
| "everything I've changed" | Run `git status --short` to list all changed paths |

If you cannot resolve it confidently, **ask the user** — do not guess.

---

## Step 4 — Commit Message Details

### Check staged content first

Before composing the message, check what's staged in the worktree:

```bash
git -C "<wt-path>" diff --staged
```

If nothing is staged yet, also check the unstaged diff — `wtcmt` will run
`git add -A` first anyway:

```bash
git -C "<wt-path>" diff
```

### Multi-line messages

For a multi-line message (subject + body), pass it as one quoted argument with
embedded newlines:

```bash
bash <skill-dir>/scripts/wtcmt "<wt-path>" "feat(scope): add feature

Detailed body here."
```

If the message contains single quotes or is otherwise awkward to quote, write
it to a file under `.wt-pr/temp/` and pass `@<path>` instead (see
[Temp File Conventions] in SKILL.md).

### Commit message style

Produce a **Conventional Commits** message in the configured language, e.g.
`refactor(core): delete old parser, adjust new parser signature`. Match the
repo's existing commit style for type/scope conventions.

---

## Step 5 — Capture Remote Branch Name

On push success, capture the remote branch name the `wtpush` script reports.
This is useful for tracking and for Step 6 PR description.

---

## Step 6 — PR Content Details

### PR content must cover the full branch

The PR title and body must represent **every** change in the branch diff — every
file added, modified, or deleted, every functional change. Do not write a PR
that only covers the most recent commit or a subset of changes. A PR that omits
changes is misleading; it represents the full branch.

### Model PR on existing repo PRs

If `PR模板路径` exists in `commit.md`, read that template and fill it.
Otherwise, model the title/body on the repo's existing open or merged PRs:

```bash
gh pr list --state all --limit 10
gh pr view <num>
```

Generate title + body in the configured `PR语言`.

### Conflict detection for PR preferences

When checking whether `PR语言` or `PR格式` contradicts reality, inspect
existing PRs:

```bash
gh pr list --state all --limit 10
```

If a contradiction is found, follow the conflict detection procedure in
`references/preferences.md` — stop and ask the user.

### Long or quote-heavy PR bodies

For long or quote-heavy bodies, write the body to a file under `.wt-pr/temp/`
and pass `@<path>` as the body arg:

```bash
bash <skill-dir>/scripts/wtpr "<wt-path>" "<base>" "<title>" "@.wt-pr/temp/pr-body.txt"
```

---

## Step 7 — CI Fix Loop Tips

When inspecting failing CI checks:

```bash
gh pr checks "<PR_URL>"
gh run view <run-id> --log-failed
```

For a faster root-cause, consider reusing the `gh-actions-debug` skill. Use
`codegraph` tools to locate the code that needs fixing.

---

## Step 8 — Non-Success Handling

In every situation **other than** full success (a step failed, CI not green,
hits a retry limit, or the user paused):

- **Leave the doc in `activate/`** so it can be resumed.
- Set `清理标志` → `待清理` to indicate the worktree can be removed later.
- Concurrency is the user's responsibility — the skill takes no locks.

---

## Temp Files — Why Not System Temp?

On Windows the system temp directory (`C:\Users\…\AppData\Local\Temp`) may be on
a **different drive** from the repo (`E:\…`). Git worktree paths and `@`-file
references must be reachable from the worktree's working directory; cross-drive
paths can confuse tools or require different quoting. A repo-local temp dir
(`.wt-pr/temp/`) avoids this entirely and keeps cleanup trivial (just delete
the file after use — or don't, the whole `temp/` dir is gitignored).
