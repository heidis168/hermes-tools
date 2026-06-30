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

我加载 `agents-orchestrator` 角色定义，按它的 4 阶段工作流顺序执行。每个"生成智能体"步骤适配为一个 `delegate_task` 调用。

**关键区别**：我不是一批派发所有子代理，而是**一次一个，我控制循环**。

## 适配规则

| agents-orchestrator 原文 | Hermes 适配 |
|---|---|
| "生成一个 XX 智能体来完成任务" | `delegate_task(goal=任务描述, context=角色定义, toolsets=[...])` |
| 开发-QA 循环 | 我在主循环控制：实现→验证→失败→重做→验证…… |
| "生成一个 XX 智能体来测试" | `delegate_task(goal=验证任务, context=测试角色定义, toolsets=[...])` |
| 失败回退 | 我判断验证结果，决定是否重新派发实现任务 |
| 状态报告 | 我维护进度变量 |

## 执行流程

### 阶段 1：项目分析与规划
```
delegate_task(goal="分析需求并创建任务清单", role=project-manager-senior)
```

### 阶段 2：技术架构
```
delegate_task(goal="设计技术架构和规范", role=engineering-software-architect)
```

### 阶段 3：开发-QA 循环（我在主循环控制）
```
for each task:
  max_retries = 3
  while retries < max_retries:
    result = delegate_task(goal=实现任务, role=对应开发者)
    verdict = delegate_task(goal=验证任务, role=对应测试员)
    if verdict == PASS: break
    retries += 1
```

### 阶段 4：集成验证
```
delegate_task(goal="最终集成验证", role=testing-reality-checker)
```

## 角色库

`~/.ao-roles/` 或插件内置 `agents/` 目录。用 `ao_roles_load(slug)` 加载角色定义后注入子代理的 context。
