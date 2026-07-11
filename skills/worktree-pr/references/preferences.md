# Preferences File: `commit.md` Schema & Resolution Rules

## Schema

`commit.md` is located at `.wt-pr/commit.md`, maintained by both the user and the Agent in UTF-8.

### Required Keys

| Key | Values | Description |
|-----|--------|-------------|
| 分支格式 | Comma-separated patterns, e.g. `feat/<ticket>-<short-desc>, fix/<short-desc>` | Branch naming convention |
| 提交语言 | `中文` or `英文` | Language for commit messages |
| PR语言 | `中文` or `英文` | Language for PR titles and bodies |

### Optional Keys

| Key | Description |
|-----|-------------|
| 提交格式 | Custom commit message format string |
| 提交模板路径 | Path to a commit template file |
| PR格式 | Custom PR body format string |
| PR模板路径 | Path to a PR template file |

Additional free-form prose preferences may be appended on their own lines.

## Who Creates & Updates

- **Creates**: the Agent at Step 2 / Step 4 if `commit.md` does not yet exist.
- **Updates**: either party at any time. The Agent updates when:
  1. A required key is missing and resolved via the fallback chain below.
  2. The user explicitly requests a change.

## Fallback Chain for Missing Keys

When `commit.md` is missing or lacks a required key, resolve in order:

1. **Project config files** — `.commitlintrc*`, `cz-config.js`, `.github/COMMIT_TEMPLATE.md`, PR templates under `.github/`
2. **Existing repo conventions** — the naming/style of existing branches and merged PRs
3. **Ask the user** — the final fallback

Write the resolved value back into `commit.md` so later runs don't re-ask.

## Conflict Detection

When the Agent discovers a value in `commit.md` **contradicts** observable reality in the repo, it must **stop and ask the user immediately** — do not silently follow `commit.md` and do not silently ignore it.

### Contradiction Examples

- `提交语言: 英文` but existing commit messages are consistently in Chinese (or vice versa).
- `分支格式: feat/<short-desc>` but the repo's actual branch names consistently follow a different pattern like `feature/<ticket>-<desc>`.
- `PR语言: 中文` but all existing PRs use English titles and bodies.

### Resolution

On detection, ask a concrete question:

> `commit.md` says `提交语言: 英文`, but I see that all recent commits in this repo use Chinese messages. Which should I follow?

Then update `commit.md` with the user's answer to keep future runs consistent.
