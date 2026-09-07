---
name: commit-objectively
description: >
  Generate and execute Git commits based strictly on the diff since the last commit
  or against a specified base branch. Stages relevant changes and commits with an
  objectively generated message that follows project conventions. Use when: (1)
  "commit these changes", (2) "write a commit message", (3) "generate commit from diff",
  (4) "help me commit", (5) user asks to commit current changes, (6) 提交指定文件,
  (7) 提交所有更改, (8) 提交变更. Make sure to use this skill whenever the user
  mentions commits, commit messages, git commit, or wants to commit changes (including
  "提交", "commit", "commit these files", "commit all changes"), even if they don't
  explicitly say "commit".
---

# Commit Objectively

Generate a commit message from the diff alone, then execute the commit.

The message comes from the diff — not from what the user said, not from what you
infer. This keeps the commit history accurate and reviewable without needing to
remember conversation context.

`<skill_directory>` is the parent directory of this SKILL.md.

## How it works

1. **Gather context**: Run `<skill_dir>/scripts/ctx.cmd` (Windows) or `<skill_dir>/scripts/ctx.sh` (Unix)
   to fetch upstream and see recent commit style.

2. **Determine diff base**: Use `HEAD~1` by default, or the branch the user
   specifies (e.g., `origin/main`, `develop`).

3. **Stage changes**: Add relevant files (`git add`), excluding private files
   (`.env*`, `*.key`, `node_modules/`, `target/`, `dist/`, `*.log`).
   Unstage everything else. If the user names specific files, stage only those.

4. **Read the diff**: `git diff --cached` (or `git diff HEAD` / `git diff <base>`
   if nothing is staged).

5. **Write the commit message** from the diff:
   - Subject: objective summary of all changes, imperative mood
   - Type/scope: follow project conventions from `git log -10 --no-author`;
     fall back to Conventional Commits (feat, fix, docs, style, refactor, perf,
     test, build, ci, chore, revert)
   - Body: if the change isn't obvious from the subject, describe what changed
     file by file — this helps reviewers without requiring background context
   - Footer: `BREAKING CHANGE:` if the diff shows incompatible API changes;
     reference issues if the branch name indicates one

6. **Write to temporary file**: Save the commit message to a temporary file
   (e.g., `.git/COMMIT_EDITMSG_TMP.txt`) to ensure consistent line endings across
   platforms. The file should contain the subject, an empty line, then the body
   (if any) and footer (if any).

7. **Review with user**:
   - Check if the user explicitly requests to skip confirmation (phrases like
     "commit directly", "no confirm", "--no-verify", "yes commit", etc.). If so,
     proceed directly to step 8.
   - Otherwise, try to open the temporary file for the user to review:
     * On Windows: `start "" "<temp-file>"` or `notepad "<temp-file>"`
     * On macOS: `open "<temp-file>"`
     * On Linux: `xdg-open "<temp-file>"` or appropriate editor command
   - If terminal commands are not available in the current environment, inform
     the user of the temporary file location and ask them to review it manually.
   - Ask for confirmation before proceeding.

8. **Execute**: When user confirms or if skip was requested, run
   `git commit -F "<temp-file>"` then clean up the temporary file.

## What to avoid

- Don't ask "what did you change?" — the diff has the answer.
- Don't include conversation content in the message.
- Don't infer intent beyond what the diff shows.
- Don't hardcode the diff base — determine it from context.
- If the diff is empty, stop and tell the user.
