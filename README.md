# Skills Repository

A collection of agent skills for [Claude Code](https://claude.ai/code) and compatible CLI tools.

> Spec: [Agent Skills Specification](https://agentskills.io/specification)
> Created via: [Skill Creator](https://www.skills.sh/anthropics/skills/skill-creator)
> [![skills.sh](https://skills.sh/b/SunYanbox/skills)](https://skills.sh/SunYanbox/skills)

## Install

```bash
npx skills add SunYanbox/skills
```

## Skills

| Skill | Description |
| --- | --- |
| [commit-formatter-zh-cn](skills/commit-formatter-zh-cn/SKILL.md) | Formats Git commit messages per Conventional Commits — type/scope in English, description/body/footer in Chinese |
| [commit-objectively](skills/commit-objectively/SKILL.md) | Generate and execute Git commits based strictly on the diff — stages changes, generates an objective commit message from the diff, then commits |
| [gh-actions-debug](skills/gh-actions-debug/SKILL.md) | Debugs GitHub Actions workflow failures fast — fetches logs, errors, and workflow YAML with a single command |
| [pr-pilot](skills/pr-pilot/SKILL.md) | One-click PR creation with project-aware AI generation — learns conventions, generates content, creates PR via throwaway worktree |
| [pr-objectively](skills/pr-objectively/SKILL.md) | Generate Pull Request content based strictly on the diff — gathers project context (PR templates, labels, recent PRs), generates objective PR title/body/labels, then creates the PR |
| [worktree-pr](skills/worktree-pr/SKILL.md) | Isolate uncommitted changes into a pull request using a throwaway git worktree — commit, push, open PR, and babysit CI to green |
| [pdf-production](skills/pdf-production/SKILL.md) | PDF generation and processing — three production lines (Report/Academic/Process) with built-in OFL fonts, layout conventions, and quality verification |

### pr-pilot

Automates the full PR workflow with AI-generated content. Analyzes project conventions (branch format, commit style, PR language), confirms with you, then generates a branch name, commit message, and PR title/body aligned to those conventions. A single scripted command creates a throwaway worktree, copies files, commits, pushes, and opens the PR — with built-in resume support if interrupted.

### pr-objectively

Generates Pull Request content based strictly on the diff against the target base branch. Gathers project context (PR templates, labels, recent PRs) to produce an objective PR title, body, and label set, then executes `gh pr create`. The content comes from the diff — not from what you said or inferred — keeping PRs reviewable without needing to remember conversation context.

### commit-formatter-zh-cn

Standardizes Git commit messages for Chinese-speaking teams. Supports two modes:

- **Manual**: user describes changes, skill formats them
- **Auto**: reads `git diff` to analyze and generate commit messages

Uses Conventional Commits types (`feat`, `fix`, `docs`, etc.) with Chinese descriptions.

### commit-objectively

Generates and executes Git commits based strictly on the diff since the last commit or against a specified base branch. Stages relevant changes and commits with an objectively generated message that follows project conventions. The message comes from the diff — not from what you said — keeping commit history accurate and reviewable without needing to remember conversation context.

### gh-actions-debug

Diagnoses failing GitHub Actions workflows in minimal steps. Fetches all relevant data (run metadata, job logs, error extracts, workflow YAML) in a single bash call, then analyzes and provides a targeted fix recommendation.

### worktree-pr

Isolates a subset of uncommitted changes into a clean pull request without disturbing your current working tree. Uses a throwaway git worktree on a fresh branch, copies selected files, commits (squashed), pushes, opens a PR, and watches CI to green. Bundled scripts enable step-by-step or fully automated execution.

> To avoid frequent interruptions to the user, you may need to enable automatic modes such as `auto mode on` and `YOLO mode on`. (Manual execution is still recommended for the first run, to ensure that any automatically retrieved information—such as language and rules—aligns with the actual situation, or to correct any erroneous rules summarized by the Agent.)
