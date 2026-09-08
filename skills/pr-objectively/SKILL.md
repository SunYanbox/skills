---
name: pr-objectively
description: >
  Generate Pull Request content based strictly on the diff against the target base
  branch and create the PR. Gathers project context (PR templates, labels, recent PRs)
  to produce an objective PR title, body, and label set, then executes `gh pr create`.
  Use when: (1) "create a PR", (2) "generate PR description", (3) "turn this into a PR",
  (4) "write a pull request", (5) user wants to create a PR from current changes, (6)
  创建PR, (7) 基于指定分支创建PR, (8) 推送并创建PR. Make sure to use this skill whenever
  the user mentions PRs, pull requests, or wants to create one (including "创建PR",
  "create PR from branch", "push and create PR", "基于main创建PR"), even if they don't
  explicitly say "create PR".
---

# PR Objectively

Generate PR title, body, and labels from the diff alone.

The PR content comes from the diff — not from what the user said, not from what
you infer. This keeps PRs reviewable without needing to remember conversation
context.

`<skill_directory>` is the parent directory of this SKILL.md.

## How it works

1. **Gather context (first-time only)**: Run `<skill_dir>/scripts/ctx.cmd` (Windows) or `<skill_dir>/scripts/ctx.sh` (Unix)
   to get project conventions. This script only needs to be run once per skill session; it does not need to be re-run for each PR creation:
   - Labels from `gh label list`
   - PR template (or "No template found")
   - Recent merged/open/closed PRs (style, language, base branches)
   - Current branch name

2. **Determine base branch**: Infer from recent PRs' `baseRefName`, default to
   `main`, or use what the user specifies.

3. **Read the diff**: `git diff <base>...HEAD` and `git diff --name-status <base>...HEAD`.

4. **Write the PR content** from the diff:
   - **Title**: objective summary of all changes, imperative mood, follow project
     PR title style
   - **Body**:
     - If template exists: fill every section based on the diff; write "N/A" for
       sections that don't apply
     - If no template: follow style from recent PRs — typically Summary, Changes
       (file-by-file), Testing, Related Issues
     - The body is a detailed description of **what** changed, so reviewers
       understand without background context
   - **Labels**: Select from `gh label list` output based on the change type
     (bug fix → bug label, new feature → feature label, etc.)

5. **Write to temporary file**: Save the PR body to a temporary file
   (e.g., `.git/PR_BODY_TMP.txt`) to ensure consistent line endings across platforms.
   Write the body content exactly as generated, including all formatting.

6. **Execute**: Run the PR creation command and clean up the temporary file.

## What to avoid

- Don't ask "what did you change?" — the diff has the answer.
- Don't include conversation content in the PR.
- Don't infer intent beyond what the diff shows.
- Don't hardcode labels — always use `gh label list` output.
- Don't hardcode the base branch — infer or ask the user.
- Don't include CHANGELOG reminders — that's project-specific.
- If the diff is empty, stop and tell the user.
