# 技能仓库

适用于 [Claude Code](https://claude.ai/code) 及兼容 CLI 工具的 agent 技能集合。

> 规范：[Agent Skills Specification](https://agentskills.io/specification)
> 创建工具：[Skill Creator](https://www.skills.sh/anthropics/skills/skill-creator)

## 安装

```bash
npx skills add SunYanbox/skills
```

## 技能列表

| 技能 | 描述 |
|------|------|
| [commit-formatter-zh-cn](skills/commit-formatter-zh-cn/SKILL.md) | 基于 Conventional Commits 规范格式化 Git 提交信息——type/scope 使用英文，description/body/footer 使用中文 |
| [gh-actions-debug](skills/gh-actions-debug/SKILL.md) | 快速调试 GitHub Actions 工作流失败——单个命令获取日志、错误信息和工作流 YAML |
| [worktree-pr](skills/worktree-pr/SKILL.md) | 将未提交的更改隔离到独立的 Pull Request 中——使用临时 git worktree 提交、推送、创建 PR 并监控 CI 直至通过 |

### commit-formatter-zh-cn

面向中文团队的 Git 提交信息标准化工具。支持两种工作模式：

- **手动模式**：用户描述变更内容，技能格式化为规范信息
- **自动模式**：读取 `git diff` 分析变更并生成提交信息

采用 Conventional Commits 标准类型（`feat`、`fix`、`docs` 等），描述使用中文。

### gh-actions-debug

以最少步骤诊断 GitHub Actions 工作流失败原因。通过单个 bash 命令获取所有相关数据（运行元数据、任务日志、错误摘要、工作流 YAML），然后分析并给出针对性的修复建议。

### worktree-pr

将部分未提交更改隔离到独立的 Pull Request 中，不影响当前工作树。使用临时 git worktree 在全新分支上操作，复制选定文件、压缩提交、推送、创建 PR 并监控 CI 直至通过。配套脚本支持逐步执行或全自动执行。

> 为避免频繁打扰用户，可能需要启用 `auto mode on`、`YOLO mode on` 等自动模式（首次执行仍建议手动操作，以确保自动搜索到的语言、规则等信息与实际情况一致，或用以纠正 Agent 总结出的错误规则）。
