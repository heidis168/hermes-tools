# Hermes Tools

Hermes Agent 的插件和技能合集。

## 目录结构

```
hermes-tools/
├── plugins/                 # 插件
│   ├── remote-ssh/          # SSH 远程服务器管理插件
│   └── ao-roles/            # 自动角色匹配引擎插件
├── skills/                  # 技能
│   ├── remote-ssh-parallel/ # 远程 SSH 操作指南
│   ├── computer-use-setup/  # Computer Use 跨平台配置指南
│   └── ao-roles/            # 自动角色匹配工作流引擎
├── README.md
└── .gitignore
```

---

## 安装方法

### 1. 装插件

```bash
# remote-ssh
hermes plugins install heidis168/hermes-tools/plugins/remote-ssh
hermes plugins enable remote-ssh

# ao-roles
hermes plugins install heidis168/hermes-tools/plugins/ao-roles
hermes plugins enable ao-roles
```

更新插件：

```bash
hermes plugins update remote-ssh
hermes plugins update ao-roles
```

插件损坏时，强制重装：

```bash
hermes plugins install heidis168/hermes-tools/plugins/remote-ssh --force
hermes plugins enable remote-ssh
```

### 2. 装技能

```bash
hermes skills install heidis168/hermes-tools/skills/remote-ssh-parallel
hermes skills install heidis168/hermes-tools/skills/computer-use-setup
hermes skills install heidis168/hermes-tools/skills/ao-roles
```

更新技能：

```bash
hermes skills update remote-ssh-parallel
hermes skills update computer-use-setup
hermes skills update ao-roles
```

技能损坏时，强制重装：

```bash
hermes skills install heidis168/hermes-tools/skills/remote-ssh-parallel --force
```

### 3. 安装角色库（ao-roles 专用）

装完 ao-roles 插件后，需要准备角色定义文件：

```bash
# 方式一：从 GitHub 克隆（推荐，可更新）
git clone --depth 1 https://github.com/jnMetaCode/agency-agents-zh.git ~/.ao-roles

# 方式二：设置自定义路径
export AO_ROLES_DIR=/your/path/to/roles
```

首次使用前构建索引：

```bash
python3 ~/.ao-roles/scripts/build_index.py
# 或通过插件工具：ao_roles_index()
```

---

## 插件列表

### remote-ssh

通过 SSH 管理远程服务器的 Hermes 插件，提供 8 个工具：

| 工具 | 功能 |
|------|------|
| `remote_connect` | 建立 SSH 连接（密码或密钥认证） |
| `remote_disconnect` | 断开 SSH 连接 |
| `remote_exec` | 在远程服务器执行命令 |
| `remote_sudo` | 以 sudo 权限执行命令 |
| `remote_info` | 探测远程服务器环境信息 |
| `remote_health` | 检查 SSH 连接健康状态 |
| `remote_list` | 查看当前连接状态 |
| `remote_set_cwd` | 设置远程工作目录 |

#### 使用示例

```python
# 连接
remote_connect(host="192.168.1.1", port=22, username="root", password="***")

# 执行命令
remote_exec(command="df -h")
remote_exec(command="lsblk")

# 获取环境信息
remote_info()

# 断开
remote_disconnect()
```

#### 并行操作多台服务器

使用 `delegate_task` 可同时操作多台服务器：

```python
delegate_task(tasks=[
    {"goal": "检查服务器 A 磁盘", "toolsets": ["remote-ssh"], "context": "IP=..., 密码=..."},
    {"goal": "检查服务器 B 磁盘", "toolsets": ["remote-ssh"], "context": "IP=..., 密码=..."},
])
```

详细用法见 `skills/remote-ssh-parallel/SKILL.md`。

---

### ao-roles

自动角色匹配引擎插件。根据输入内容，从 266 个专业角色中自动匹配最合适的角色阵容，配合 `delegate_task` 派生子代理执行。

提供 5 个工具：

| 工具 | 功能 |
|------|------|
| `ao_roles_index` | 构建/刷新角色索引 |
| `ao_roles_search` | 按关键词搜索角色 |
| `ao_roles_match` | 根据任务描述自动匹配角色阵容 |
| `ao_roles_load` | 加载指定角色的完整定义（用于注入子代理 context） |
| `ao_roles_list_categories` | 列出所有角色分类 |

#### 使用流程

```
① ao_roles_index()           → 构建索引
② ao_roles_match(task=...)   → 自动匹配角色阵容
③ ao_roles_load(slug=...)    → 加载每个角色的完整定义
④ delegate_task(goal=..., context=角色人格, toolsets=[...])  → 派生子代理执行
```

#### 完整示例

```python
# 1. 构建索引
ao_roles_index()

# 2. 匹配角色
match = ao_roles_match(task="审查 src/auth/login.ts 的安全性和代码质量")
# 返回：code-reviewer, security-tester, backend-architect

# 3. 加载角色定义
role_reviewer = ao_roles_load(slug="engineering-code-reviewer")
role_security = ao_roles_load(slug="security-penetration-tester")
role_architect = ao_roles_load(slug="engineering-backend-architect")

# 4. 派生子代理（并行）
results = delegate_task(tasks=[
    {"goal": "审查代码质量", "context": role_reviewer, "toolsets": ["terminal", "file"]},
    {"goal": "安全审查",     "context": role_security, "toolsets": ["terminal", "file", "web"]},
])

# 5. 汇总
delegate_task(
    goal="综合输出最终审查报告",
    context=f"{role_architect}\n\n审查：{results[0]}\n安全：{results[1]}",
    toolsets=["file"],
)
```

详细用法见 `skills/ao-roles/SKILL.md` 和 `skills/ao-roles/references/delegate-task-pattern.md`。

---

## 技能列表

### remote-ssh-parallel

配套 `remote-ssh` 插件的使用指南，涵盖：
- 主会话直连操作
- `delegate_task` 并行操作多台服务器
- 批量模式（最多 5 台并行）
- 已知 BUG 与修复记录

### computer-use-setup

在任意平台上配置 Hermes `computer_use` 桌面控制功能的跨平台指南，涵盖：
- cua-driver 安装与后台服务配置
- MCP 服务器注册与超时调优
- Windows：git-bash PATH 修复、pywin32 缺失陷阱
- Linux / macOS：待补充
- 端到端验证与故障排除速查表

### ao-roles

自动角色匹配工作流引擎技能。配合 `ao-roles` 插件使用，提供完整的执行流程指引：
- 内容分析 → 角色匹配 → DAG 编排 → delegate_task 子代理执行 → 汇总
- 4 个完整示例（代码审查、登录系统、营销内容、架构分析）
- 工具集选择指南
- 详见 `skills/ao-roles/references/delegate-task-pattern.md`
