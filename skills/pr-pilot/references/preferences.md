# Preferences File: `.pr-pilot/preferences.md` Schema & Resolution Rules

## Schema

`.pr-pilot/preferences.md` is maintained by both the user and the Agent in UTF-8.

### Required Keys

| Key | Values | Description |
|-----|--------|-------------|
| 分支格式 | Comma-separated patterns, e.g. `feat/<short-desc>, fix/<short-desc>` | Branch naming convention |
| 提交语言 | `中文` or `英文` | Language for commit messages |
| PR语言 | `中文` or `英文` | Language for PR titles and bodies |

### Optional Keys

| Key | Description |
|-----|-------------|
| 提交格式 | Commit style description, e.g. "Conventional Commits" |
| PR格式 | Custom PR body format string |
| PR模板路径 | Path to a PR template file (e.g. `.github/PULL_REQUEST_TEMPLATE.md`) |
| 其他偏好 | Free-form additional preferences |

### File Format

The file uses simple key-value lines:

```
- 分支格式: feat/<short-desc>, fix/<short-desc>
- 提交语言: 中文
- PR语言: 英文
- 提交格式: Conventional Commits (type(scope): description)
- PR格式: ## Summary\n## Changes\n## Testing
- PR模板路径: .github/PULL_REQUEST_TEMPLATE.md
- 其他偏好: Always include a "Breaking changes" section if applicable
```

## Who Creates & Updates

- **Creates**: the Agent at Step 1 (项目偏好) after analyzing the repo and confirming with the user.
- **Updates**: either party at any time. The Agent updates when:
  1. A required key is missing and resolved via the fallback chain below.
  2. The user explicitly requests a change.
  3. Conflict detection reveals a contradiction — after user resolution.

## Fallback Chain for Missing Keys

When `preferences.md` is missing or lacks a required key, resolve in order:

1. **Project config files** — `.commitlintrc*`, `cz-config.js`, `.github/COMMIT_TEMPLATE.md`, PR templates under `.github/`
2. **Existing repo conventions** — the naming/style of existing branches (`git branch -a`), commit messages (`git log --oneline -30`), and merged PRs (`gh pr list --state all --limit 10`)
3. **Ask the user** — the final fallback with concrete options based on what you observed

Write the resolved value back into `preferences.md` so later runs don't re-ask.

## Conflict Detection

When the Agent discovers a value in `preferences.md` **contradicts** observable reality in the repo, it must **stop and ask the user immediately** — do not silently follow `preferences.md` and do not silently ignore it.

### Contradiction Examples

- `提交语言: 英文` but existing commit messages are consistently in Chinese (or vice versa).
- `分支格式: feat/<short-desc>` but the repo's actual branch names consistently follow a different pattern like `feature/<ticket>-<desc>`.
- `PR语言: 中文` but all existing PRs use English titles and bodies.

### Resolution

On detection, ask a concrete question:

> preferences.md says `提交语言: 英文`, but I see that all recent commits in this repo use Chinese messages. Which should I follow?

Then update `preferences.md` with the user's answer to keep future runs consistent.

## Memory Integration

After saving preferences for the first time, also save a `project` memory about the project's Git/PR conventions. Use a descriptive name like `project-git-conventions` so future sessions can retrieve it and potentially skip the analysis step. Link back to the preferences file path.
