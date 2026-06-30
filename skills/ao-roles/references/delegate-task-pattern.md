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

## 示例 2：登录系统全套（6 角色，3 路并行）

```
输入："做一个登录系统 全套"

DAG：
  step_1 (UX) ──→  step_2 (后端) ──→  step_5 (安全) ──→  step_6 (测试)
                ──→  step_3 (前端) ──→       ↑
                ──→  step_4 (数据库) ──→     ↑
  (step_2/3/4 并行)

执行：
  # 第 1 批：UX 架构师（先导）
  ux_result = delegate_task(
    goal="作为 UX 架构师，设计登录系统的用户流程和交互规范",
    context=role_ux_context,
    toolsets=["file"],
  )

  # 第 2 批：后端 + 前端 + 数据库 并行
  results_2_4 = delegate_task(tasks=[
    {
        "goal": "作为后端架构师，设计认证 API",
        "context": f"{role_backend_context}\n\nUX 设计：{ux_result}",
        "toolsets": ["terminal", "file"],
    },
    {
        "goal": "作为前端开发者，实现登录 UI",
        "context": f"{role_frontend_context}\n\nUX 设计：{ux_result}",
        "toolsets": ["terminal", "file"],
    },
    {
        "goal": "作为数据库优化师，设计用户表 Schema",
        "context": f"{role_db_context}\n\nUX 设计：{ux_result}",
        "toolsets": ["terminal", "file"],
    },
  ])

  # 第 3 批：安全审查（依赖上一步全部输出）
  security_result = delegate_task(
    goal="作为安全工程师，对登录系统进行安全审查",
    context=f"{role_security_context}\n\nAPI 设计：{results_2_4[0]}\nUI 实现：{results_2_4[1]}\n数据库 Schema：{results_2_4[2]}",
    toolsets=["terminal", "file", "web"],
  )

  # 第 4 批：API 测试（依赖安全审查）
  test_result = delegate_task(
    goal="作为 API 测试员，对认证 API 进行全面测试",
    context=f"{role_tester_context}\n\n安全审查结果：{security_result}",
    toolsets=["terminal", "file"],
  )

  # 汇总（主代理执行）
  final_report = f"""
# 登录系统全套交付物

## UX 设计
{ux_result}

## 后端 API
{results_2_4[0]}

## 前端 UI
{results_2_4[1]}

## 数据库 Schema
{results_2_4[2]}

## 安全审查
{security_result}

## API 测试
{test_result}
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
