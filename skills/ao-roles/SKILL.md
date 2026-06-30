---
name: ao-roles
description: 自动角色匹配工作流引擎——输入内容，自动从 266 个专业角色中匹配最合适的角色阵容，编排 DAG 工作流，每个角色通过 delegate_task 作为独立子代理使用真实工具执行
---

# AO-Roles 自动角色匹配工作流引擎

## 概述

根据用户输入的内容（需求描述、代码、文档、项目路径等），自动分析、匹配角色、编排工作流并执行。**每个角色通过 `delegate_task` 作为独立子代理运行**，拥有完整的工具调用能力（`terminal`、`read_file`、`search_files`、`web_search` 等）。

> ⚠️ **核心原则**：每个角色必须是真正的子代理（`delegate_task`），拥有独立的工具调用上下文。**禁止主代理一人分饰多角**——每个步骤必须是真实的工具执行，而非对话扮演。

## 角色库位置

角色定义文件在插件内置的 `agents/` 目录中（装插件即自带，无需额外 clone）。

也可通过环境变量 `AO_ROLES_DIR` 指定自定义路径。

角色索引由 `ao_roles_index()` 工具自动构建。

## 前置条件

- `delegation` 工具集必须启用（`hermes tools enable delegation`）
- 当前会话需要 `/reset` 后才能使用 `delegate_task`

## 执行流程

### 第 1 步：加载角色索引

读取 `~/.ao-roles/role-index.json` 获取所有角色信息。
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

根据角色间的依赖关系生成工作流。无依赖的步骤可并行执行（通过批量 `delegate_task`）。

### 第 5 步：通过 delegate_task 执行

每个步骤使用 `delegate_task` 派生子代理执行：

```python
# 单步子代理
delegate_task(
    goal="作为 {角色名}，完成以下任务：{具体任务描述}",
    context="""你的角色定义：
{读取 ~/.ao-roles/{category}/{slug}.md 的完整内容}

上游输出：
{如果有依赖，传入上游步骤的输出}

任务要求：
- 使用真实工具（read_file / terminal / search_files / web_search 等）完成任务
- 输出具体、可验证的结果
- 不要只做对话回复，必须执行真实操作""",
    toolsets=["terminal", "file", "web"],  # 根据任务类型选择合适的工具集
)

# 并行执行（无依赖的步骤）
delegate_task(
    tasks=[
        {"goal": "...", "context": "...", "toolsets": [...]},
        {"goal": "...", "context": "...", "toolsets": [...]},
    ]
)
```

**关键规则**：
- 子代理的 `context` 中必须包含完整的角色人格定义（从 `.md` 文件读取）
- 子代理的 `toolsets` 根据任务类型选择（代码审查用 `terminal`+`file`，内容创作用 `web` 等）
- 无依赖的步骤通过 `tasks=[]` 批量并行
- 每个子代理的 goal 要明确要求"使用真实工具，不要只做对话"

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
