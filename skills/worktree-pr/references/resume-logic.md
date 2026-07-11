# Resume Logic for Step 0

When scanning `.wt-pr/activate/` for in-progress task docs matching the
current branch, the Agent must distinguish between two user scenarios **before**
deciding whether to resume an existing task or start a new one.

## A. User did NOT specify a file scope

(e.g. "make a PR for my changes" — no files/dirs mentioned)

| Situation | Action |
|-----------|--------|
| Exactly one in-progress doc exists | Ask: "Found an in-progress task (`<name>`). Continue it, or start a new one?" If continue → resume from the first `待办`/`进行中`/`失败` step. If new → proceed to Step 1. |
| Multiple in-progress docs exist | List them and ask the user which one to continue. The Agent must **not** operate on two worktrees simultaneously without the user's explicit choice. |
| No in-progress doc exists | Tell the user: no in-progress task found and no file scope specified. Ask which files to include in the PR before proceeding to Step 1. |

## B. User specified a clear file scope

(e.g. "commit and push src/core" — concrete files/dirs mentioned)

| Situation | Action |
|-----------|--------|
| One in-progress doc's change scope **exactly matches** the user's scope | Ask: "Found an in-progress task (`<name>`) with the same file scope. Continue it?" If yes → resume; if no → proceed to Step 1 to start a new task. |
| No in-progress doc matches the scope | Proceed directly to Step 1 (start a new task without asking). |
| Multiple docs partially overlap | Treat as no exact match and proceed to Step 1. |

## General resume rules

- Find the first step not marked `[完成]`. Re-run that step's script — scripts
  with idempotency checks (`wtcmt`) will safely skip already-done work.
- Update the task doc to reflect reality before proceeding.
- Concurrency is the user's responsibility — the skill takes no locks, but the
  Agent must never operate on two worktrees at once without the user choosing.
