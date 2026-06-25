# Hermes Tools

Hermes Agent 的插件和技能合集。

## 目录结构

```
hermes-tools/
├── plugins/                 # Hermes 插件
│   └── remote-ssh/          # SSH 远程服务器管理插件
├── skills/                  # Hermes 技能
│   └── remote-ssh-parallel/ # 远程 SSH 操作指南（与插件配套使用）
└── README.md
```

---

## 前置条件：安装 Hermes Agent

如果你还没有 Hermes Agent，先安装它：

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

安装完成后，运行 `hermes setup` 完成初始配置，或直接开始使用。

---

## 安装方法

### 1. 安装插件（remote-ssh）

**方式一：hermes plugins install（推荐）**

```bash
git clone https://github.com/heidis168/hermes-tools.git
hermes plugins install ./hermes-tools/plugins/remote-ssh
```

**方式二：手动复制**

```bash
git clone https://github.com/heidis168/hermes-tools.git
cp -r hermes-tools/plugins/remote-ssh ~/.hermes/plugins/
```

安装后，在 Hermes 中启用工具集：

```bash
hermes tools enable remote-ssh
```

> 插件依赖 `paramiko`，加载时会自动安装。如果自动安装失败，手动执行：
> ```bash
> pip install paramiko
> ```

### 2. 安装技能（remote-ssh-parallel）

**方式一：hermes skills install（推荐）**

```bash
hermes skills install https://raw.githubusercontent.com/heidis168/hermes-tools/main/skills/remote-ssh-parallel/SKILL.md
```

**方式二：手动复制**

```bash
cp -r hermes-tools/skills/remote-ssh-parallel ~/.hermes/skills/devops/
```

加载技能：

```
/skill remote-ssh-parallel
```

或启动时加载：

```bash
hermes -s remote-ssh-parallel
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

---

## 开发

```bash
# 克隆
git clone https://github.com/heidis168/hermes-tools.git
cd hermes-tools

# 插件代码结构
plugins/remote-ssh/
├── __init__.py      # 插件入口，注册 8 个工具
├── tools.py         # 工具处理函数
├── ssh_manager.py   # SSH 连接管理器（单例，线程安全）
├── schemas.py       # 工具参数 schema
└── plugin.yaml      # 插件元信息

# 技能文档结构
skills/remote-ssh-parallel/
└── SKILL.md         # 使用指南
```
