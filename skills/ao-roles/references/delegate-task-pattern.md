# AO-Roles 工作流参考

## agents-orchestrator 适配对照

| agents-orchestrator 原文 | Hermes 适配 |
|---|---|
| "生成一个 project-manager-senior 智能体来读取规格说明并创建任务列表" | 加载 `project-manager-senior` 角色定义 → `read_file` 读需求 → `write_file` 写任务清单 |
| "生成一个 ArchitectUX 智能体来创建技术架构" | 加载 `design-ux-architect` 或 `engineering-software-architect` 角色定义 → `write_file` 写架构文档 |
| "生成合适的开发者智能体来实现任务" | 加载对应角色定义（frontend/backend/etc）→ `write_file` 写代码 → `terminal` 运行 |
| "生成 EvidenceQA 智能体来测试" | 加载 `testing-api-tester` 或 `testing-reality-checker` 角色定义 → `terminal` 跑测试 |
| "截图证据" | `terminal` 命令输出作为证据 |
| "标记任务完成" | 更新进度变量 |

## 执行示例：登录系统

### 阶段 1：项目分析与规划
```
加载 project-manager-senior 角色
→ 分析"做一个登录系统全套"
→ 输出：login-system-tasklist.md（任务清单）
```

### 阶段 2：技术架构
```
加载 engineering-software-architect 角色
→ 根据任务清单创建技术规范
→ 输出：API 设计文档、数据库 Schema
```

### 阶段 3：开发-QA 循环
```
任务 1：加载 backend-architect → 实现认证 API → write_file → terminal 验证
任务 2：加载 frontend-developer → 实现登录 UI → write_file → terminal 验证
任务 3：加载 database-optimizer → 设计表结构 → write_file → terminal 验证
...
每个任务实现后，加载 testing-api-tester → 验证 → 失败则回实现步骤
```

### 阶段 4：集成验证
```
加载 testing-reality-checker → 最终验证 → 输出报告
```
