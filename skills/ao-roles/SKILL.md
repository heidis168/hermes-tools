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

加载 `agents-orchestrator`（智能体编排者）角色定义，按它的 4 阶段工作流执行。

```
role = ao_roles_load(slug="agents-orchestrator")
# 按 role 中的阶段 1→2→3→4 顺序执行
```
