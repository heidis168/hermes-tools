---
name: ao-roles
description: 自动角色匹配工作流引擎
activation:
  gate: strict
  conditions:
    - 用户明确要求多角色协作
    - 任务复杂度中等以上
  examples_skip:
    - "帮我写一个函数"
    - "这个bug怎么修"
---

# AO-Roles 工作流引擎

## 工作方式

我（主 Agent）加载 `agents-orchestrator` 的角色定义，按它的 4 阶段工作流顺序执行。每个阶段加载对应角色的 `.md` 定义，使用真实工具完成任务。

## 执行流程

### 阶段 1：项目分析与规划

加载 `project-manager-senior` 角色定义 → 分析需求 → 创建任务清单（写文件）

### 阶段 2：技术架构/基础

加载对应领域的架构角色定义 → 创建技术基础和规范（写文件）

### 阶段 3：开发-QA 循环

对每个任务：
1. 加载对应角色定义 → 实现（写代码/文件）
2. 加载测试角色定义 → 验证（跑测试）
3. 失败则回到步骤 1，最多 3 次

### 阶段 4：集成验证

加载 `testing-reality-checker` 角色定义 → 最终验证 → 输出报告

## 适配规则

| agents-orchestrator 原文 | Hermes 适配 |
|---|---|
| "生成一个 XX 智能体" | 加载 `~/.ao-roles/{category}/{slug}.md` 作为当前人格 |
| 智能体用工具完成任务 | 我用 `read_file`/`write_file`/`terminal` 执行 |
| 开发-QA 循环 | 实现步骤 → 测试步骤 → 失败则回实现步骤 |
| 截图证据 | `terminal` 跑测试命令的输出作为证据 |
| 状态报告 | 维护进度变量，每步输出状态 |

## 角色库

`~/.ao-roles/` 或插件内置 `agents/` 目录。用 `ao_roles_load(slug)` 加载。
