# Skills Repository

A collection of agent skills for [Claude Code](https://claude.ai/code) and compatible CLI tools.

> Spec: [Agent Skills Specification](https://agentskills.io/specification)
> Created via: [Skill Creator](https://www.skills.sh/anthropics/skills/skill-creator)

## Install

```bash
npx skills add SunYanbox/skills
```

## Skills

| Skill | Description |
| --- | --- |
| [commit-formatter-zh-cn](skills/commit-formatter-zh-cn/SKILL.md) | Formats Git commit messages per Conventional Commits — type/scope in English, description/body/footer in Chinese |
| [gh-actions-debug](skills/gh-actions-debug/SKILL.md) | Debugs GitHub Actions workflow failures fast — fetches logs, errors, and workflow YAML with a single command |

### commit-formatter-zh-cn

Standardizes Git commit messages for Chinese-speaking teams. Supports two modes:

- **Manual**: user describes changes, skill formats them
- **Auto**: reads `git diff` to analyze and generate commit messages

Uses Conventional Commits types (`feat`, `fix`, `docs`, etc.) with Chinese descriptions.

### gh-actions-debug

Diagnoses failing GitHub Actions workflows in minimal steps. Fetches all relevant data (run metadata, job logs, error extracts, workflow YAML) in a single bash call, then analyzes and provides a targeted fix recommendation.
