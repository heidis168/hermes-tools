# Hermes Tools

Hermes Agent 的插件和技能合集。

## 目录结构

```
hermes-tools/
├── plugins/                 # 插件
│   └── remote-ssh/          # SSH 远程服务器管理插件
├── skills/                  # 技能
│   └── remote-ssh-parallel/ # 远程 SSH 操作指南
├── README.md
└── .gitignore
```

---

## 安装方法

### 1. 装插件

```bash
hermes plugins install heidis168/hermes-tools/plugins/remote-ssh
hermes plugins enable remote-ssh
```

更新插件：

```bash
hermes plugins update remote-ssh
```

插件损坏时，强制重装：

```bash
hermes plugins install heidis168/hermes-tools/plugins/remote-ssh --force
hermes plugins enable remote-ssh
```

### 2. 装技能

```bash
hermes skills install heidis168/hermes-tools/skills/remote-ssh-parallel
```

更新技能：

```bash
hermes skills update remote-ssh-parallel
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

## 技能列表

### remote-ssh-parallel

配套 `remote-ssh` 插件的使用指南，涵盖：
- 主会话直连操作
- `delegate_task` 并行操作多台服务器
- 批量模式（最多 5 台并行）
- 已知 BUG 与修复记录
