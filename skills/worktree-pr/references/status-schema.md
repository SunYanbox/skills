# Task Document Schema & Status Update Rules

## Step Names (枚举)

| 步骤名 | English | Description |
|--------|---------|-------------|
| 检查工具 | Tool check | Verify `git` and `gh` are on PATH |
| 创建工作树 | Create worktree | `git worktree add` on a new branch |
| 复制文件 | Copy files | Diff-copy changed files into the worktree |
| 提交 | Commit | `git add -A && git commit` in the worktree |
| 推送 | Push | Push the worktree's branch to origin |
| 创建PR | Create PR | `gh pr create` |
| CI等待与修复 | CI wait & fix | Poll CI; if red, fix → re-commit → re-push (max 3 rounds) |

## Status Values (枚举)

| 值 | English | Meaning |
|----|---------|---------|
| 待办 | Pending | Not started |
| 进行中 | In progress | Currently executing |
| 完成 | Done | Successfully finished |
| 失败 | Failed | Error encountered |

## 清理标志 Values (枚举)

| 值 | English | Meaning |
|----|---------|---------|
| 暂不清理 | No cleanup | Default; task is active |
| 待清理 | To clean | Task paused/failed; worktree can be removed later |
| 已清理 | Cleaned | Worktree has been removed |
| 已存档 | Archived | Task doc moved to `done/` |

## Task Document Template

```markdown
- 起始分支: <branch>
- 工作树名: <wt-name>
- 工作树路径: <absolute path>
- 用户要求: <user's original request, verbatim>
- 创建时间: <ISO8601 UTC timestamp>
- 步骤状态:
  - 检查工具: [待办]
  - 创建工作树: [待办]
  - 复制文件: [待办]
  - 提交: [待办]
  - 推送: [待办]
  - 创建PR: [待办]
  - CI等待与修复: [待办]
- 修复失败计数: 0
- 清理标志: 暂不清理
```

## Status Update Rules (硬性合约)

**禁止使用 Bash 更新状态**，必须通过文件编辑工具直接修改任务文档。

### 操作流程

1. 使用 **Read** 工具读取任务文档，确认当前状态。
2. 使用 **Edit** 工具精确替换 `- <步骤名>: [旧状态]` 为 `- <步骤名>: [新状态]`。

   常规流程（执行没有问题的情况下）：
   - 先将当前步骤的 `[进行中]` 替换为 `[完成]`
   - 再将下一步骤的 `[待办]` 替换为 `[进行中]`
   - 这两处替换可以在**一次 Edit 调用**中完成

3. **验证**：再次 **Read** 文档，确认替换生效。若失败需重试。

### 修复失败计数操作

`修复失败计数` 的增减通过 Read + Edit 两步完成：

1. **Read** 文档，找到 `- 修复失败计数: <N>` 行
2. **Edit** 将 `- 修复失败计数: <N>` 替换为 `- 修复失败计数: <N+1>`（递增）或目标值

### 批量更新（恢复任务时）

允许在一次 Edit 操作中完成多行替换（如将前序步骤批量标为 `[完成]`），但必须执行一次最终的 **Read** 验证。

### 清理标志

`清理标志` 是普通文本行，同样用 Edit 工具直接替换：
- `- 清理标志: 暂不清理` → `- 清理标志: 待清理`
- `- 清理标志: 暂不清理` → `- 清理标志: 已存档`

### Edit 工具的隐式验证

Edit 工具要求 `old_string` 精确匹配，这本身就提供了验证：
- 若步骤名写错，Edit 找不到匹配行会报错
- 若状态值写错，替换结果不符合预期时 Read 验证会发现
