# Step-by-Step Procedural Details

This file holds detailed procedural guidance for each workflow step. The
SKILL.md checklist items summarize **what** to do; this file explains **how**.

---

## `<skill-dir>` Substitution

`<skill-dir>` is the absolute path of the directory containing `SKILL.md`.
Substitute it everywhere (e.g. `bash /abs/path/scripts/ghchk`). When the repo
is the skills repo itself and you are at its root, `skills/pr-pilot/scripts/...`
also works. Run all scripts through the Bash tool.

---

## Step 1 — Project Preferences Analysis

### What to analyze

Run these commands to understand the repo's conventions:

```bash
# Commit style — last 30 commits
git log --oneline -30

# Branch style
git branch -a | head -30
git for-each-ref --format='%(refname:short)' refs/heads refs/remotes | head -30

# PR style — if gh is authenticated
gh pr list --state all --limit 10 --json number,title,body,headRefName 2>/dev/null
# For detail on a specific PR:
gh pr view <num> --json title,body 2>/dev/null
```

### What to extract

From the output, identify:

1. **Commit pattern**: Is there a consistent type? (feat/fix/refactor/chore/docs) Is there a scope? Is it in Chinese or English? Are ticket numbers included?
2. **Branch pattern**: What prefix is used? Separator (`/` or `-`)? Ticket numbers present? Language?
3. **PR pattern**: Title format? Body structure (sections, checklist)? Language?

### How to present to user

Summarize in natural language, not raw data. Example:

> "I looked at this repo's conventions:
> - **Branches**: `feat/xxx`, `fix/xxx`, `chore/xxx` — all English, no ticket numbers
> - **Commits**: Conventional Commits in Chinese — `feat(core): 添加新功能`
> - **PRs**: Chinese titles with detailed bullet-point bodies
>
> Does this match your project's conventions? Any adjustments?"

### Memory integration

After saving preferences, create a `project` memory:

```
E:\skills\.claude\projects\E--skills\memory\project-git-conventions.md
```

With content like:

```markdown
---
name: project-git-conventions
description: Git/PR conventions for this skills repo
metadata:
  type: project
---

Branch: feat/xxx, fix/xxx (English, no ticket).
Commit: Conventional Commits in Chinese (feat/fix/refactor).
PR: Chinese, bullet-point body.
Preferences: .pr-pilot/preferences.md
```

This allows future sessions to skip re-analysis by retrieving the memory.

---

## Step 2 — Scope Mapping Examples

| User says | Map to |
|-----------|--------|
| "the changes under `src/core`" | `src/core` (directory) |
| "the two files I just edited" | Ask: "Which two files?" |
| "everything I've changed" | `git diff --name-only HEAD` for uncommitted; `git diff --name-only <base>...HEAD` for branch changes |
| "just the auth module changes" | `src/auth/` (directory) |
| "commit abc123 and def456" | List files changed in those commits: `git diff --name-only abc123^!` and `git diff --name-only def456^!` |

If you cannot resolve it confidently, **ask the user** — do not guess.

---

## Step 3 — Diff Review

### Commands to capture diff

```bash
# Uncommitted changes (working tree vs HEAD)
git diff HEAD -- <file1> <file2> ...

# Staged changes
git diff --cached -- <file1> <file2> ...

# Branch changes (commits on top of base)
git diff <base>...HEAD -- <file1> <file2> ...

# Combined — everything not in base
git diff <base>...HEAD -- <file1> <file2> ...
```

### What to note

- Every file added, modified, or deleted
- Every functional change (not whitespace or formatting)
- Breaking changes, new dependencies, config changes
- Any TODO, FIXME, or incomplete work

---

## Step 4 — Content Generation

### Branch name generation

Given `分支格式: feat/<short-desc>, fix/<short-desc>`:

1. Determine the **type** from the diff: new feature → `feat`, bug fix → `fix`, refactor → `refactor`
2. Compose a concise hyphenated English description from the change content
3. Combine: `feat/add-login-flow`

Rules:
- Keep short-desc under ~50 chars
- Use hyphens, not underscores
- Lowercase
- Omit ticket number unless the format requires `<ticket>`
- Check `git show-ref --verify --quiet "refs/heads/<branch>"` — if exists, append `-2`, `-3`, etc., or ask user

### Commit message generation

Follow the `提交格式` and `提交语言` preferences. Default to Conventional Commits:

```
<type>(<scope>): <description>

<optional body: list of concrete changes>
```

- Type from the change: feat, fix, refactor, chore, docs, test, style, perf
- Scope from the area of change (core, ui, api, etc.)
- Description: imperative mood, present tense, no period
- Body: bullet points of each functional change (one per file/change)
- Language: per `提交语言` preference

Write to `.pr-pilot/temp/commit-msg.txt`.

### PR title and body generation

**Title**: One-line summary matching the repo's PR title convention. Typically matches or slightly expands the commit subject.

**Body**:
- Start with a summary paragraph
- List all changes with file paths
- Include any relevant context (why, what problem it solves)
- If `PR模板路径` exists, fill in that template's structure
- If no template, model on existing PRs from `gh pr list`

Write to `.pr-pilot/temp/pr-title.txt` and `.pr-pilot/temp/pr-body.txt`.

---

## Step 5 — One-Click Script Details

### When pilot.sh fails

The script prints `FAIL: <step_name>` and exits non-zero. The Agent should:

| Fail step | Likely cause | Fix |
|-----------|-------------|-----|
| `tool_check` | `git` or `gh` not installed | Install the missing tool |
| `create_worktree` | Branch name conflict or path exists | Change branch name with `git branch -D` or remove path |
| `copy_files` | File not found | Double-check scope paths with `ls` or `git ls-files` |
| `commit` | Empty staged diff or commit message | Check message content, verify files were copied |
| `push` | Network/auth | Try `git -C <wt-path> push -u origin <branch>` manually, or check `gh auth status` |
| `create_pr` | gh auth or API error | Check `gh auth status`, verify base branch exists |

After fixing the cause, re-run the exact same `pilot.sh` command — it skips completed steps via state markers.

### Manual push fallback

If `pilot.sh` push fails and you need to try SSH manually:

```bash
# Get the SSH URL
ORIGIN=$(git remote get-url origin)
SSH_URL=$(echo "$ORIGIN" | sed 's|https://github.com/|git@github.com:|' | sed 's|\.git$||').git
git -C <wt-path> remote set-url origin "$SSH_URL"
git -C <wt-path> push -u origin <branch>
# Restore original URL
git -C <wt-path> remote set-url origin "$ORIGIN"
```

---

## Step 6 — Finish & Prompt

On success, `pilot.sh` prints the PR URL. Present it clearly:

> ✅ PR created: https://github.com/owner/repo/pull/123
>
> Branch `feat/add-login` has been pushed.
>
> ⏳ **Please wait for CI to pass before merging.** You can check status with:
> `gh pr checks https://github.com/owner/repo/pull/123`

Do NOT run `gh pr checks` or any CI-watching tool — the skill intentionally stops here.

### Cleanup

Offer to clean up the worktree:

```bash
# Remove worktree
rm -rf <wt-path>
# Optionally also prune git's worktree metadata
git worktree prune
```

If user says no, leave it. They can remove it later.

### State directory after success

The `state/` directory still has its markers. This is fine — they are gitignored. If the user wants to start a fresh task later, the Agent checks for existing markers at Step 0 and asks whether to resume or start fresh. If starting fresh, remove the old markers: `rm -rf .pr-pilot/state .pr-pilot/temp`.
