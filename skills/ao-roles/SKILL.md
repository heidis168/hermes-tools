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

## 执行流程（严格算法，必须按顺序执行）

> ⚠️ **这是必须遵守的算法，不是参考指南。跳过任何一步都会导致各角色产出无法拼接。**

### 第 1 步：加载角色索引

调用 `ao_roles_index()` 确保索引存在。

### 第 2 步：分析输入内容

分析用户输入，提取 task_type。**这是后续选择规划角色的依据。**

### 第 3 步：匹配角色

用 `ao_roles_match()` 从索引中选出 2–6 个角色。

### 第 4 步：执行 4 阶段工作流（严格按此顺序）

#### ⛔ 禁止行为
- ❌ 跳过阶段 0，直接派发子代理
- ❌ 让多个角色在无统一计划的情况下各做各的
- ❌ 把阶段 0 和阶段 1 合并到同一个 delegate_task batch 中
- ❌ 用主代理"扮演"多个角色代替 delegate_task

#### ✅ 阶段 0：总项目计划（必须先执行，且仅此一个子代理）

这是整个工作流**最重要的一步**。必须单独执行，不能和任何其他任务并行。

```python
# 根据 task_type 选择规划角色
PLANNER_MAP = {
    "code_review": "engineering-software-architect",
    "architecture": "engineering-software-architect",
    "fullstack": "engineering-software-architect",
    "backend": "engineering-backend-architect",
    "frontend": "engineering-software-architect",
    "product": "product-manager",
    "project": "project-manager-senior",
    "planning": "project-manager-senior",
    "marketing": "marketing-content-strategist",
    "content": "marketing-content-strategist",
    "security": "security-architect",
    "design": "design-ux-architect",
    "data": "finance-fpa-analyst",
    "game": "game-designer",
    "ecommerce": "marketing-ecommerce-operator",
    "workflow": "specialized-workflow-architect",
}
planner_slug = PLANNER_MAP.get(task_type, "project-manager-senior")

# ★ 必须单独执行，不能和任何其他任务并行
master_plan = delegate_task(
    goal=f"作为规划角色，为项目制定总执行计划",
    context=f"...（包含角色定义 + 需求 + 输出 JSON 格式要求）...",
    toolsets=["file"],
)

# ★ 必须验证 master_plan 包含有效的 tasks 数组
# ★ 必须从 master_plan 中解析出 tasks 列表
```

#### ✅ 阶段 1：按计划分批执行

从 `master_plan` 中解析出 `tasks` 数组，按 `depends_on` 分批：

```python
plan = json.loads(master_plan)  # 解析 master_plan

# 批次 1：所有 depends_on=[] 的任务（可并行）
batch1 = [t for t in plan["tasks"] if not t["depends_on"]]
if batch1:
    r1 = delegate_task(tasks=[
        {
            "goal": t["description"],
            "context": f"角色定义：\n{ao_roles_load(slug=t['role_slug'])}\n\n总计划：\n{master_plan}\n\n你的任务：\n{t['description']}\n\n输出契约：\n{t['output_contract']}",
            "toolsets": t.get("toolsets", ["terminal", "file"]),
        }
        for t in batch1
    ])

# 批次 2：依赖批次 1 的任务
batch2 = [t for t in plan["tasks"] if t["depends_on"] and all(
    any(b["id"] == d for b in batch1) for d in t["depends_on"]
)]
if batch2:
    r2 = delegate_task(tasks=[...])  # context 中带上 batch1 的输出

# 批次 3、4……按依赖层级继续
```

#### ✅ 阶段 2：集成验证

用审查角色验证阶段 1 的所有产出是否符合 `master_plan` 中的接口契约。

#### ✅ 阶段 3：汇总

输出最终报告。

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
