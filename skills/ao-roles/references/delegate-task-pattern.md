# delegate_task 执行模式参考

## 通用模板

### 单步子代理

```python
# 1. 读取角色人格
role_content = ao_roles_load(slug=slug)

# 2. 构造 context
context = f"""# 你的角色人格

{role_content}

---

# 你的任务

{task}

---

# 上游输入

{upstream_outputs}

---

# 执行要求
- 使用真实工具（read_file / terminal / search_files / web_search 等）完成任务
- 输出具体、可验证的结果
- 不要只做对话回复，必须执行真实操作
"""

# 3. 派发子代理
result = delegate_task(
    goal=f"作为{role_name}，{task_summary}",
    context=context,
    toolsets=["terminal", "file", "web"],
)
```

### 并行子代理（batch 模式）

```python
tasks = [
    {
        "goal": "作为后端架构师，设计认证 API",
        "context": role_backend_context,
        "toolsets": ["terminal", "file"],
    },
    {
        "goal": "作为前端开发者，实现登录 UI",
        "context": role_frontend_context,
        "toolsets": ["terminal", "file"],
    },
]

# 同时派发，最多 5 个并发
results = delegate_task(tasks=tasks)
# results[0] = 后端架构师输出
# results[1] = 前端开发者输出
```

---

## 示例 1：代码审查（3 角色，2 路并行）

```
输入："审查 src/auth/login.ts 的安全性和代码质量"

DAG：
  step_1 (code-reviewer)  ──→  step_3 (architect, 汇总)
  step_2 (security)       ──→       ↑
  (step_1 和 step_2 并行)

执行：
  # 第 1 批：并行派发代码审查 + 安全审查
  results_1_2 = delegate_task(tasks=[
    {
        "goal": "作为代码审查员，审查 login.ts 的代码质量",
        "context": role_reviewer_context,
        "toolsets": ["terminal", "file"],
    },
    {
        "goal": "作为安全工程师，审查 login.ts 的安全风险",
        "context": role_security_context,
        "toolsets": ["terminal", "file", "web"],
    },
  ])

  # 第 2 批：汇总
  result_3 = delegate_task(
    goal="作为后端架构师，综合输出最终审查报告",
    context=f"代码审查结果：{results_1_2[0]}\n\n安全审查结果：{results_1_2[1]}\n\n{role_architect_context}",
    toolsets=["file"],
  )
```

---

## 示例 2：登录系统全套（4 阶段，严格串行→并行→串行）

```
输入："做一个登录系统 全套"

阶段 0: 统一架构（先导，仅此一个角色）
  └── 后端架构师 → 定义 API 规范、数据 Schema、技术栈
      输出：architecture_spec（所有下游角色共享）

阶段 1: 并行执行（依赖阶段 0）
  ├── 后端架构师 → 按 architecture_spec 实现 API
  ├── 前端开发者 → 按 architecture_spec 实现 UI
  └── 数据库优化师 → 按 architecture_spec 设计表

阶段 2: 交叉审查（依赖阶段 1）
  ├── 安全工程师 → 审查 API + UI + Schema
  └── API 测试员 → 根据规范测试 API

阶段 3: 汇总
  └── 输出最终报告

执行：
  # ══════════════════════════════════════
  # 阶段 0: 统一架构（必须先执行）
  # ══════════════════════════════════════
  architect_role = ao_roles_load(slug="engineering-backend-architect")
  architecture_spec = delegate_task(
      goal="作为后端架构师，为登录系统定义统一架构规范",
      context=f"""你的角色定义：
{architect_role}

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

  # ══════════════════════════════════════
  # 阶段 1: 并行执行（所有角色共享 architecture_spec）
  # ══════════════════════════════════════
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

  # ══════════════════════════════════════
  # 阶段 2: 交叉审查（依赖阶段 1 全部输出）
  # ══════════════════════════════════════
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

  # ══════════════════════════════════════
  # 阶段 3: 汇总
  # ══════════════════════════════════════
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

---

## 示例 3：营销内容创作（4 角色，2 路并行）

```
输入："写一篇关于 AI 编程工具对比的公众号文章"

DAG：
  step_1 (策略师) ──→  step_3 (创作者) ──→  step_4 (设计师)
  step_2 (SEO)    ──→       ↑
  (step_1 和 step_2 并行)

执行：
  # 第 1 批：策略 + SEO 并行
  results_1_2 = delegate_task(tasks=[
    {
        "goal": "作为内容策略师，制定文章策略和大纲",
        "context": role_strategist_context,
        "toolsets": ["web", "file"],
    },
    {
        "goal": "作为 SEO 专家，做关键词研究",
        "context": role_seo_context,
        "toolsets": ["web", "file"],
    },
  ])

  # 第 2 批：内容创作
  content = delegate_task(
    goal="作为内容创作者，撰写公众号文章",
    context=f"{role_creator_context}\n\n策略：{results_1_2[0]}\nSEO 关键词：{results_1_2[1]}",
    toolsets=["file"],
  )

  # 第 3 批：配图设计
  delegate_task(
    goal="作为 UI 设计师，设计文章配图",
    context=f"{role_designer_context}\n\n文章内容：{content}",
    toolsets=["file"],
  )
```

---

## 示例 4：项目架构分析（4 角色，2 路并行）

```
输入："分析这个项目的整体架构，给出优化建议"

DAG：
  step_1 (架构师) ──→  step_3 (DevOps)  ──→  step_4 (汇总)
  step_2 (数据库) ──→  step_3 (代码审查) ──→       ↑
  (step_1/2 并行，step_3 内 DevOps/审查 并行)

执行：
  # 第 1 批：架构分析 + 数据库分析 并行
  results_1_2 = delegate_task(tasks=[
    {
        "goal": "作为后端架构师，分析项目架构",
        "context": role_architect_context,
        "toolsets": ["terminal", "file"],
    },
    {
        "goal": "作为数据库优化师，分析数据库设计",
        "context": role_db_context,
        "toolsets": ["terminal", "file"],
    },
  ])

  # 第 2 批：DevOps + 代码审查 并行
  results_3 = delegate_task(tasks=[
    {
        "goal": "作为 DevOps 专家，分析部署和运维",
        "context": f"{role_devops_context}\n\n架构：{results_1_2[0]}",
        "toolsets": ["terminal", "file", "web"],
    },
    {
        "goal": "作为代码审查员，审查代码质量",
        "context": f"{role_reviewer_context}\n\n架构：{results_1_2[0]}\n数据库：{results_1_2[1]}",
        "toolsets": ["terminal", "file"],
    },
  ])

  # 汇总
  delegate_task(
    goal="汇总所有分析结果，输出优化建议报告",
    context=f"架构：{results_1_2[0]}\n数据库：{results_1_2[1]}\nDevOps：{results_3[0]}\n代码审查：{results_3[1]}",
    toolsets=["file"],
  )
```

---

## 工具集速查

| 角色分类 | toolsets | 典型任务 |
|---------|----------|---------|
| engineering/* | `["terminal", "file"]` | 读代码、跑分析、审查 |
| security/* | `["terminal", "file", "web"]` | 扫描、查 CVE、安全审查 |
| marketing/* | `["web", "file"]` | 搜索资料、写文案 |
| design/* | `["file"]` | 写设计规范、CSS |
| testing/* | `["terminal", "file"]` | 跑测试、写测试用例 |
| product/* | `["file", "web"]` | 写 PRD、调研 |
| finance/* | `["terminal", "file", "web"]` | 数据分析、报表 |
| specialized/* | `["terminal", "file", "web"]` | 按需 |
