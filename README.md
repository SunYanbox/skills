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
| [gh-actions-debug](skills/gh-actions-debug/SKILL.md) | Debugs GitHub Actions workflow failures fast — fetches logs, errors, and workflow YAML with a single command |
| [worktree-pr](skills/worktree-pr/SKILL.md) | Isolate uncommitted changes into a pull request using a throwaway git worktree — commit, push, open PR, and babysit CI to green |

### commit-formatter-zh-cn

Standardizes Git commit messages for Chinese-speaking teams. Supports two modes:

- **Manual**: user describes changes, skill formats them
- **Auto**: reads `git diff` to analyze and generate commit messages

Uses Conventional Commits types (`feat`, `fix`, `docs`, etc.) with Chinese descriptions.

### gh-actions-debug

Diagnoses failing GitHub Actions workflows in minimal steps. Fetches all relevant data (run metadata, job logs, error extracts, workflow YAML) in a single bash call, then analyzes and provides a targeted fix recommendation.

### worktree-pr

Isolates a subset of uncommitted changes into a clean pull request without disturbing your current working tree. Uses a throwaway git worktree on a fresh branch, copies selected files, commits (squashed), pushes, opens a PR, and watches CI to green. Bundled scripts enable step-by-step or fully automated execution.

> To avoid frequent interruptions to the user, you may need to enable automatic modes such as `auto mode on` and `YOLO mode on`. (Manual execution is still recommended for the first run, to ensure that any automatically retrieved information—such as language and rules—aligns with the actual situation, or to correct any erroneous rules summarized by the Agent.)
