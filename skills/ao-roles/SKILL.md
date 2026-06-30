---
name: ao-roles
description: 自动角色匹配工作流引擎——输入内容，自动从 266 个专业角色中匹配最合适的角色阵容，编排 DAG 工作流，每个角色通过 delegate_task 作为独立子代理使用真实工具执行
activation:
  gate: strict
  conditions:
    - 用户明确要求"多角色协作"、"工作流"、"自动匹配角色"、"子代理"、"ao-roles" 等关键词
    - 任务复杂度为中等以上，需要 3 个以上专业角色协作完成
    - 简单任务（单文件编辑、单问题回答、单命令执行）禁止激活此技能
  examples_trigger:
    - "审查这个项目的架构，需要多个角色协作"
    - "做一个登录系统全套，自动匹配角色"
    - "帮我分析这个代码库，让不同专家各司其职"
  examples_skip:
    - "帮我写一个函数"
    - "这个bug怎么修"
    - "什么是delegate_task"
    - "当前目录有什么文件"
    - "安装xxx"
---

# AO-Roles 自动角色匹配工作流引擎

## ⚠️ 激活条件（必须全部满足才激活）

此技能加载到上下文会消耗 token，**仅在以下条件全部满足时激活**：

### ✅ 必须同时满足
1. **用户明确要求多角色协作** — 包含"多角色"、"工作流"、"自动匹配"、"子代理"、"ao-roles"、"角色阵容"、"各司其职"、"让不同专家" 等关键词
2. **任务复杂度 ≥ 中等** — 需要 3 个以上专业角色协作，涉及多个领域
3. **非简单任务** — 不是单文件编辑、单问题回答、单命令执行

### ✅ 应该激活的例子
- "审查这个项目的架构，需要多个角色协作"
- "做一个登录系统全套，自动匹配角色"
- "帮我分析这个代码库，让不同专家各司其职"
- "用产品经理+架构师+测试的角色阵容分析这个PR"

### ❌ 不应该激活的例子
- "帮我写一个函数" → 单步任务
- "这个bug怎么修" → 单步排查
- "什么是delegate_task" → 知识问答
- "当前目录有什么文件" → 简单查询
- "安装xxx" → 单步操作
- "翻译这段文字" → 单步任务

### 如果误激活
直接说"不需要多角色"即可关闭此技能的工作流模式，退回普通模式。

---

## 概述

根据用户输入的内容（需求描述、代码、文档、项目路径等），自动分析、匹配角色、编排工作流并执行。**每个角色通过 `delegate_task` 作为独立子代理运行**，拥有独立的工具调用上下文。

> ⚠️ **核心原则**：每个角色必须是真正的子代理（`delegate_task`），拥有独立的工具调用上下文。**禁止主代理一人分饰多角**——每个步骤必须是真实的工具执行，而非对话扮演。

## 角色库位置

角色定义文件在插件内置的 `agents/` 目录中（装插件即自带，无需额外 clone）。

也可通过环境变量 `AO_ROLES_DIR` 指定自定义路径。

角色索引由 `ao_roles_index()` 工具自动构建（插件内置 `agents/` 目录）。

## 读取角色定义

使用插件工具 `ao_roles_load(slug=...)` 加载角色完整定义，不要直接读文件路径。

## 前置条件

- `delegation` 工具集必须启用（`hermes tools enable delegation`）
- 当前会话需要 `/reset` 后才能使用 `delegate_task`

## 执行流程

### 第 1 步：加载角色索引

使用插件工具 `ao_roles_index()` 构建索引，或通过 `ao_roles_search()` / `ao_roles_match()` 直接搜索匹配角色。

每个角色包含：slug, name, description, emoji, category, filepath, summary

### 第 2 步：分析输入内容

分析用户输入，提取：
- **任务类型**：code_review / architecture_analysis / content_creation / security_audit / marketing / planning / testing / research / ...
- **领域**：engineering / marketing / design / finance / security / product / ...
- **关键词和技术栈**
- **复杂度**：low / medium / high
- **是否需要并行**

### 第 3 步：匹配角色

从 266 个角色中选出最合适的 2–6 个角色。匹配依据：
1. 角色 `name` 和 `description` 与任务类型的语义匹配度
2. 角色 `category` 与任务领域的匹配度
3. 角色的 `summary`（正文前 300 字）中的专业领域

**输出**：按相关性排序的角色列表，每个角色附带匹配理由和推荐任务。

### 第 4 步：编排工作流 DAG

**核心原则：必须先有总项目计划，再有按计划执行。**

所有多角色工作流必须遵循以下通用 4 阶段结构：

```
阶段 0: 总项目计划（必须最先执行，且仅此一个角色）
  └── 项目规划角色 制定：
      - 任务分解（WBS）：把大任务拆成可独立执行的子任务
      - 依赖关系：哪些子任务必须先完成，哪些可以并行
      - 接口契约：子任务之间的交付物格式/协议/约定
      - 角色分配：每个子任务分配给哪个角色
      - 输出：master_plan（所有下游角色共享的执行蓝图）

阶段 1: 按计划执行（依赖阶段 0 的 master_plan）
  ├── 角色 A → 按 master_plan 中分配的 task_A 执行
  ├── 角色 B → 按 master_plan 中分配的 task_B 执行
  ├── 角色 C → 按 master_plan 中分配的 task_C 执行
  └── ...（所有角色按同一份计划工作，依赖关系由计划定义）

阶段 2: 集成验证（依赖阶段 1 的输出）
  ├── 审查角色 → 验证各子任务产出是否符合 master_plan 中的接口契约
  └── 测试角色 → 按 master_plan 中的验收标准测试

阶段 3: 汇总（依赖阶段 2 的输出）
  └── 输出最终报告
```

**禁止**：让多个角色在无统一计划的情况下各做各的，然后期望它们能拼在一起。

**关键**：阶段 0 的 `master_plan` 必须包含明确的**接口契约**——即子任务之间的交付物格式约定。这样即使各角色并行执行，最终产出也能无缝拼接。

### 第 5 步：通过 delegate_task 执行

每个步骤使用 `delegate_task` 派生子代理执行。

**关键规则**：
- **阶段 0（总项目计划）必须先执行**，生成所有下游角色共享的 `master_plan`
- 阶段 1 的每个子代理的 context 中**必须包含完整的 `master_plan`**，特别是自己负责的子任务和接口契约
- 阶段 2 的审查角色**必须拿到阶段 1 的全部输出**才能做有效验证
- 子代理的 `toolsets` 根据任务类型选择

```python
# ════════════════════════════════════════════════════════════
# 阶段 0: 总项目计划（先导，仅此一个角色）
# ════════════════════════════════════════════════════════════
# 选择最合适的规划角色（产品经理/架构师/项目经理，取决于任务类型）
planner_slug = "product/product-manager"  # 或 engineering-backend-architect 等
planner_role = ao_roles_load(slug=planner_slug)

master_plan = delegate_task(
    goal=f"作为规划角色，为任务制定总项目计划",
    context=f"""你的角色定义：
{planner_role}

你的任务：
为以下需求制定完整的项目执行计划：

【需求描述】
{用户输入的内容}

【要求】
1. 任务分解（WBS）：把大任务拆成可独立执行的子任务，每个子任务分配一个角色
2. 依赖关系：明确每个子任务的前置依赖，标注哪些可以并行
3. 接口契约：定义子任务之间的交付物格式/协议/约定，确保各角色产出能拼接
4. 角色分配：每个子任务指定具体角色 slug

输出格式（严格按此 JSON 结构）：
{{
  "project_name": "项目名称",
  "tasks": [
    {{
      "id": "task-1",
      "role_slug": "engineering-backend-architect",
      "description": "任务描述",
      "depends_on": [],
      "output_contract": "本任务输出的格式约定",
      "toolsets": ["terminal", "file"]
    }},
    ...
  ]
}}
""",
    toolsets=["file"],
)

# 解析 master_plan 获取任务列表
import json
plan = json.loads(master_plan)  # 实际需要从 delegate_task 返回值中提取

# ════════════════════════════════════════════════════════════
# 阶段 1: 按计划执行
# ════════════════════════════════════════════════════════════
# 按依赖关系分批执行
# 第 1 批：无依赖的任务（可并行）
batch_1_tasks = [t for t in plan["tasks"] if not t["depends_on"]]
batch_1_results = delegate_task(tasks=[
    {
        "goal": f"作为角色，完成：{t['description']}",
        "context": f"你的角色定义：\n{ao_roles_load(slug=t['role_slug'])}\n\n总项目计划：\n{master_plan}\n\n你的子任务：\n{t['description']}\n\n输出契约：\n{t['output_contract']}\n\n必须严格按输出契约格式交付。",
        "toolsets": t.get("toolsets", ["terminal", "file"]),
    }
    for t in batch_1_tasks
])

# 第 2 批：依赖第 1 批的任务
batch_2_tasks = [t for t in plan["tasks"] if t["depends_on"] and all(
    any(b["id"] == dep for b in batch_1_tasks) for dep in t["depends_on"]
)]
if batch_2_tasks:
    batch_2_results = delegate_task(tasks=[
        {
            "goal": f"作为角色，完成：{t['description']}",
            "context": f"你的角色定义：\n{ao_roles_load(slug=t['role_slug'])}\n\n总项目计划：\n{master_plan}\n\n你的子任务：\n{t['description']}\n\n上游输出：\n{batch_1_results}\n\n输出契约：\n{t['output_contract']}",
            "toolsets": t.get("toolsets", ["terminal", "file"]),
        }
        for t in batch_2_tasks
    ])

# ... 按依赖层级继续执行后续批次

# ════════════════════════════════════════════════════════════
# 阶段 2: 集成验证
# ════════════════════════════════════════════════════════════
# 根据 master_plan 中的接口契约验证各子任务产出

# ════════════════════════════════════════════════════════════
# 阶段 3: 汇总
# ════════════════════════════════════════════════════════════
```

### 第 6 步：汇总输出

收集所有子代理的输出，生成最终报告。

## 角色匹配策略

| 输入关键词 | 推荐角色分类 |
|-----------|-------------|
| 代码审查、安全、性能 | engineering/security |
| 架构设计、系统设计 | engineering |
| 营销文案、内容策略 | marketing |
| UI/UX、设计系统 | design |
| 产品规划、需求分析 | product |
| 测试、QA | testing |
| 数据分析、报表 | finance/academic |
| 项目管理、流程 | project-management |
| 安全审计、渗透 | security |
| 供应链、物流 | supply-chain |
| GIS、地图 | gis/spatial-computing |
| 游戏开发 | game-development/unity/unreal-engine |
| 技术支持 | support |
| 销售策略 | sales |
| 人力资源 | hr |
| 法律合规 | legal |

### 角色数量规则

- 简单任务（单文件审查）：2–3 个角色
- 中等任务（功能分析）：3–4 个角色
- 复杂任务（项目级分析）：4–6 个角色

## 工具集选择指南

| 任务类型 | 推荐 toolsets |
|---------|--------------|
| 代码审查/架构分析 | `["terminal", "file"]` |
| 安全审计 | `["terminal", "file", "web"]` |
| 内容创作/研究 | `["web", "file"]` |
| 数据库设计 | `["terminal", "file"]` |
| 测试 | `["terminal", "file"]` |
| 设计/UX | `["file"]` |

## 示例

### 示例 1：代码审查
输入：`"审查 src/auth/login.ts 的安全性和代码质量"`
匹配角色：
1. `engineering-code-reviewer`（代码审查）→ toolsets: `["terminal", "file"]`
2. `security-penetration-tester`（安全审查）→ toolsets: `["terminal", "file"]`（与 1 并行）
3. `engineering-backend-architect`（汇总）→ toolsets: `["file"]`（依赖 1+2）

### 示例 2：项目架构分析
输入：`"分析这个项目的整体架构，给出优化建议"`
匹配角色：
1. `engineering-backend-architect`（架构分析）
2. `engineering-database-optimizer`（数据库优化）
3. `engineering-devops-automator`（部署和运维）
4. `engineering-code-reviewer`（代码质量）

### 示例 3：营销内容创作
输入：`"写一篇关于 AI 编程工具对比的公众号文章"`
匹配角色：
1. `marketing-content-strategist`（内容策略）
2. `marketing-seo-specialist`（SEO 优化）
3. `marketing-content-creator`（内容创作）
4. `design-ui-designer`（配图设计）

## 注意

- **不要一人分饰多角**——每个角色必须通过 `delegate_task` 作为独立子代理执行
- 不要一次性加载所有 266 个角色到上下文——只加载匹配到的角色的完整定义
- 子代理的 `context` 中必须包含角色人格定义（从 `.md` 文件读取完整内容）
- 无依赖的步骤通过 `tasks=[]` 批量并行执行
- 执行失败时重试 1 次，仍失败则跳过并记录
- 参考 `hermes-delegation` 技能了解 `delegate_task` 的详细用法
