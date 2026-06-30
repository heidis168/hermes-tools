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

加载 `agents-orchestrator`（智能体编排者）角色定义，按它的 4 阶段工作流执行。每个"派发子代理"步骤使用 `delegate_task`。

## 执行流程

### 阶段 1：项目分析与规划
`delegate_task(project-manager-senior → 创建任务清单)`

### 阶段 2：技术架构
`delegate_task(design-ux-architect → 创建技术架构)`

### 阶段 3：开发-QA 循环
```
for each task:
  retries = 0
  while retries < 3:
    delegate_task(对应开发者 → 实现)
    verdict = delegate_task(对应测试员 → 验证)
    if PASS: break
    retries += 1
```

### 阶段 4：集成验证
`delegate_task(testing-reality-checker → 最终验证)`

## 角色定义

完整工作流算法见 `specialized/agents-orchestrator.md`（已适配 Hermes 版）。
