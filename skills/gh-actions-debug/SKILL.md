---
name: gh-actions-debug
description: >
  Debug GitHub Actions workflow failures fast. Use when CI builds fail, tests break
  in GitHub Actions, workflow runs error out, or any "why did the check fail" scenario.
  Trigger signals: user pastes a GitHub Actions run URL, says "CI is failing" / "build
  is broken" / "workflow failed", pastes an error from a workflow step, or asks to
  check the latest CI run without a URL (skill auto-finds recent failures automatically).
  Also triggers on: build failure, CI failure, GitHub Actions error, workflow run
  failure, pipeline breakage in a GitHub Actions context.
---

# gh-actions-debug

Diagnose failing GitHub Actions workflows. **Speed is critical** — minimize tool calls.

Scripts in `<skill-dir>/scripts/` handle data fetching. Use them — never write inline bash chains.

> **Path note**: `<skill-dir>` is the directory containing this SKILL.md. For subagents running from the repo root, prefix with `skills/gh-actions-debug/`.

## Method

### 1. Identify the run

Parse `https://github.com/{owner}/{repo}/actions/runs/{run_id}` from the URL. If no URL, use `gh run list --limit 5 --status failure --json databaseId,headBranch,workflowName,conclusion,url`.

### 2. Fetch all data (1 bash call)

```bash
bash <skill-dir>/scripts/fetch-run.sh {owner} {repo} {run_id} {output_dir}
```

If running from repo root: `bash skills/gh-actions-debug/scripts/fetch-run.sh ...`

Produces: `run.json`, `jobs.json`, `job.log`, `errors.txt`, `workflow.yml`. Takes ~5s.

### 3. Read & analyze (2 reads)

1. Read `{output_dir}/errors.txt` — error lines pre-extracted
2. Read `{output_dir}/workflow.yml` — find the failed step definition

If an error references source files (e.g., `src/foo.ts:42`), fetch only that file:

```bash
bash <skill-dir>/scripts/fetch-file.sh {owner} {repo} {path} {branch}
```

### 4. Report (1 write)

Output:

````markdown
## Failure: <workflow> / <job> / <step>

**Run #<id>** on `<branch>` · <event> · `<sha>`  
**Error:** [one-line summary]

### Root Cause
[1-2 paragraphs]

### Error
```
[Key lines from errors.txt — under 15 lines]
```

### Fix
[Specific recommendation + code suggestion]

```suggestion
// code change
```

### Verify
Re-run the workflow.
````

**Don't** offer multiple fix options. **Don't** ask to implement. **Don't** read extra files.

## Common error signals

| Log line | Likely cause |
|---|---|
| `::error::...` | Structured error — read the message body |
| `exit code 1` | Step command failed |
| `Resource not accessible by integration` | GITHUB_TOKEN permissions |
| `Cannot find module` / `not found` | Missing dependency |
| `The operation was canceled` | Timeout (check `timeout-minutes`) |
| `No space left on device` | Runner disk full |

## Edge cases

- **gh not authenticated**: Run `gh auth status` first. If it fails, tell user.
- **Run in progress**: `status != "completed"` — report and stop.
- **Multi-job failures**: Check `needs:` in workflow YAML. Report the earliest failing job.
