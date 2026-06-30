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

**核心原则：必须先有统一架构，再有并行执行。**

所有多角色工作流必须遵循以下阶段：

```
阶段 0: 统一架构（必须最先执行，且仅此一个角色）
  └── 架构师/产品经理 定义：
      - API 接口规范（端点、请求/响应格式）
      - 数据 Schema（字段名、类型、约束）
      - 技术栈选型
      - 输出：architecture_spec（所有下游角色共享）

阶段 1: 并行执行（依赖阶段 0 的输出）
  ├── 后端开发者 → 按 architecture_spec 实现 API
  ├── 前端开发者 → 按 architecture_spec 实现 UI
  ├── 数据库优化师 → 按 architecture_spec 设计表
  └── ...（所有角色共享同一份规范）

阶段 2: 交叉审查（依赖阶段 1 的输出）
  ├── 安全工程师 → 审查 API + UI + Schema
  └── 测试员 → 根据 API 规范写测试

阶段 3: 汇总（依赖阶段 2 的输出）
  └── 输出最终报告
```

**禁止**：让多个角色在无统一规范的情况下各做各的，然后期望它们能拼在一起。

### 第 5 步：通过 delegate_task 执行

每个步骤使用 `delegate_task` 派生子代理执行。

**关键规则**：
- **阶段 0（统一架构）必须先执行**，生成所有下游角色共享的 `architecture_spec`
- 阶段 1 的每个子代理的 context 中**必须包含完整的 `architecture_spec`**，确保字段名、接口路径、数据格式一致
- 阶段 2 的审查角色**必须拿到阶段 1 的全部输出**才能做有效审查
- 子代理的 `toolsets` 根据任务类型选择

```python
# ════════════════════════════════════════════════════════════
# 阶段 0: 统一架构（先导，仅此一个角色）
# ════════════════════════════════════════════════════════════
architect_role = ao_roles_load(slug="engineering-backend-architect")
architecture_spec = delegate_task(
    goal="作为后端架构师，为登录系统定义统一架构规范",
    context=f"""你的角色定义：
{architect_role}

你的任务：
为登录系统定义以下统一规范，所有下游角色将共享此规范：

1. API 接口规范
   - 端点路径、HTTP 方法、请求/响应 JSON 格式
   - 认证方式（JWT / Session）
   - 错误码规范

2. 数据 Schema
   - 用户表字段名、类型、约束
   - Token 表结构
   - 字段命名约定（snake_case / camelCase）

3. 技术栈
   - 后端语言/框架
   - 前端框架
   - 数据库

输出格式必须是结构化的 JSON/YAML 规范，所有下游角色直接引用。""",
    toolsets=["file"],
)

# ════════════════════════════════════════════════════════════
# 阶段 1: 并行执行（所有角色共享 architecture_spec）
# ════════════════════════════════════════════════════════════
backend_role = ao_roles_load(slug="engineering-backend-architect")
frontend_role = ao_roles_load(slug="engineering-frontend-developer")
db_role = ao_roles_load(slug="engineering-database-optimizer")

results_phase1 = delegate_task(tasks=[
    {
        "goal": "作为后端架构师，按统一规范实现认证 API",
        "context": f"你的角色定义：\n{backend_role}\n\n统一架构规范：\n{architecture_spec}\n\n严格按以上规范实现，字段名、路径、格式必须一致。",
        "toolsets": ["terminal", "file"],
    },
    {
        "goal": "作为前端开发者，按统一规范实现登录 UI",
        "context": f"你的角色定义：\n{frontend_role}\n\n统一架构规范：\n{architecture_spec}\n\nAPI 接口和数据格式必须与规范完全一致。",
        "toolsets": ["terminal", "file"],
    },
    {
        "goal": "作为数据库优化师，按统一规范设计 Schema",
        "context": f"你的角色定义：\n{db_role}\n\n统一架构规范：\n{architecture_spec}\n\n表名、字段名、类型必须与规范一致。",
        "toolsets": ["terminal", "file"],
    },
])

# ════════════════════════════════════════════════════════════
# 阶段 2: 交叉审查（依赖阶段 1 全部输出）
# ════════════════════════════════════════════════════════════
security_role = ao_roles_load(slug="engineering-security-engineer")
tester_role = ao_roles_load(slug="testing-api-tester")

results_phase2 = delegate_task(tasks=[
    {
        "goal": "作为安全工程师，审查登录系统的安全性",
        "context": f"你的角色定义：\n{security_role}\n\n统一架构规范：\n{architecture_spec}\n\n后端实现：{results_phase1[0]}\n前端实现：{results_phase1[1]}\n数据库Schema：{results_phase1[2]}",
        "toolsets": ["terminal", "file", "web"],
    },
    {
        "goal": "作为 API 测试员，根据规范测试认证 API",
        "context": f"你的角色定义：\n{tester_role}\n\n统一架构规范：\n{architecture_spec}\n\n后端实现：{results_phase1[0]}",
        "toolsets": ["terminal", "file"],
    },
])

# ════════════════════════════════════════════════════════════
# 阶段 3: 汇总
# ════════════════════════════════════════════════════════════
final_report = f"""
# 登录系统交付报告

## 统一架构规范
{architecture_spec}

## 后端 API
{results_phase1[0]}

## 前端 UI
{results_phase1[1]}

## 数据库 Schema
{results_phase1[2]}

## 安全审查
{results_phase2[0]}

## API 测试
{results_phase2[1]}
"""
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
