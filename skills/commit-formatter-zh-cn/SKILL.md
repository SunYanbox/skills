---
name: commit-formatter-zh-cn
description: >
  用于规范 Git commit 提交信息的 skill。基于 Conventional Commits 规范，type 和 scope 使用英文，
  description/body/footer 使用中文。当用户提到"写 commit"、"提交信息"、"格式化 commit"、"提交代码"、
  "生成提交信息"、"帮我写提交"等表达时触发。支持两种工作方式：（1）用户描述变更内容后格式化为合规信息；
  （2）自动读取 git diff 分析变更生成提交信息。
---

# Commit Formatter Skill

## 概述

生成符合规范的 Git commit 提交信息。基于 Conventional Commits 标准，type 用英文，描述用中文。

## 提交信息格式

```
<type>(<scope>): <description> (<#issue-number>)

<optional body>

<optional footer>
```

### 字段说明

| 字段 | 语言 | 规则 |
|------|------|------|
| **type** | 英文小写 | 标准 Conventional Commits types |
| **scope** | 英文小写 | 可选，描述影响范围 |
| **description** | 中文 | 简要描述变更（不超过 50 字） |
| **issue/PR 编号** | - | 如已知，追加在首行末尾 `(#123)` |
| **body** | 中文 | 可选，详细描述变更原因和影响 |
| **footer** | 中文/英文 | 可选，BREAKING CHANGE 或关联信息 |

### Types 列表（标准 Conventional Commits）

| Type | 用途 | 说明 |
|------|------|------|
| feat | 新功能 | 新增功能特性 |
| fix | 修复 Bug | 修复缺陷 |
| docs | 文档 | 仅文档变更 |
| style | 代码风格 | 不影响代码含义的变更（格式化、分号等） |
| refactor | 重构 | 既不修复 bug 也不添加功能的代码变更 |
| perf | 性能优化 | 提升性能的变更 |
| test | 测试 | 添加或修改测试 |
| build | 构建 | 构建系统或外部依赖变更 |
| ci | CI | CI 配置和脚本变更 |
| chore | 杂项 | 其他维护工作 |
| revert | 回滚 | 回滚之前的提交 |

### 完整示例

```
feat(api): 添加用户登录接口 (#42)

实现了基于 JWT 的用户登录功能，包含 token 生成和验证。
Closes #40
```

```
fix(ui): 修复首页列表加载时闪烁的问题

优化了骨架屏展示逻辑，减少不必要的重渲染。
```

```
docs: 更新 API 文档中的参数说明
```

```
refactor(core): 重构数据持久化层

将文件存储替换为数据库存储，提升数据可靠性和查询性能。
BREAKING CHANGE: 配置文件格式已变更，需要更新 config.yaml
```

## 工作模式

### 模式一：用户描述变更

用户口头描述或粘贴变更说明：

1. 理解变更内容，确定合适的 type
2. 判断 scope（如有）
3. 用中文撰写 description
4. 询问 issue/PR 编号（如未提供）
5. 输出完整 commit 信息

### 模式二：自动读取 diff

用户要求基于当前变更生成：

1. 执行 `git diff --cached`（优先）或 `git diff`
2. 分析变更的文件路径和代码内容
3. 推断 type 和 scope
4. 用中文撰写 description 和必要的 body
5. 输出完整 commit 信息

### 输出格式

用 markdown 代码块展示，方便用户直接复制使用：

```
feat(api): 添加用户登录接口

实现了基于 JWT 的用户登录功能。
```

## 注意事项

- type 必须小写，不要使用非标准 type（如 `add`、`delete`、`update`）
- description 用中文，不以句号结尾
- body 每行建议不超过 72 个字符宽度
- 中英文之间建议加空格（如"新增 JWT 认证"而非"新增JWT认证"）
