---
name: remote-ssh-parallel
description: 用 remote-ssh 插件操作远程服务器 — 主会话直连 + delegate_task 并行
version: 1.3.0
author: agent
tags: [ssh, remote, parallel, delegate, vps, devops]
---

# Remote SSH 操作指南

`remote-ssh` 插件提供 8 个工具（`remote_connect`/`remote_exec`/`remote_sudo` 等），主会话和子代理都能用。

## 主会话直连

插件装好启用了，当前会话里直接调用工具：

```
remote_connect(host="<IP>", port=<PORT>, username="root", password="<PASS>")
remote_exec(command="df -h")
remote_disconnect()
```

主会话**同一时间只能保持一个活跃连接**，新连接会自动断开旧连接。

## 子代理并行（delegate_task）

`delegate_task` 的 `toolsets` 参数接受插件注册的 toolset 名，**不限于内置工具集**。

```python
# ✅ 正确：传 toolsets=["remote-ssh"]，子代理能拿到所有 remote 工具
delegate_task(
    goal="连远程服务器，执行 df -h 和 lsblk",
    toolsets=["remote-ssh"],
    context="SSH 密码认证，端口 <PORT>，用户名 root，密码 <PASS>"
)

# ❌ 错误：只传 terminal，子代理拿不到 remote_connect
delegate_task(goal="...", toolsets=["terminal"])
```

每个子代理有独立会话环境，可以各自连不同的服务器，互不干扰。

### 批量模式（最多 5 个并行）

```python
delegate_task(tasks=[
    {"goal": "连服务器 A ...", "toolsets": ["remote-ssh"], "context": "..."},
    {"goal": "连服务器 B ...", "toolsets": ["remote-ssh"], "context": "..."},
    {"goal": "连服务器 C ...", "toolsets": ["remote-ssh"], "context": "..."},
    {"goal": "连服务器 D ...", "toolsets": ["remote-ssh"], "context": "..."},
    {"goal": "连服务器 E ...", "toolsets": ["remote-ssh"], "context": "..."},
])
```

## 注意事项

- 主会话一次只能连一台；多台并行必须用 `delegate_task`
- `max_concurrent_children` 默认 5，超过需分批次或改配置
- 子代理无法用 `clarify` 提问——所有信息放 `context` 里
- 密码等敏感信息通过 `context` 传递
- **不要在技能/代码例子里写真实 IP、端口、密码**，用 `<IP>`、`<PORT>`、`<PASS>` 占位
- **操作完毕立即断开连接**：`remote_disconnect()`，避免 SSH 连接空挂浪费资源

## 已知 BUG 与修复

### 远程主机卡死时 `remote_exec` 永久挂起（已修复）

**BUG**：`ssh_manager.py` 的 `execute()` 方法中，数据读取循环使用了 `recv_ready()` / `exit_status_ready()` 等**非阻塞**调用 + `time.sleep(0.05)` 轮询。`chan.settimeout(timeout)` 只对阻塞式 `recv()` 生效，对非阻塞轮询完全无效。当远程主机网络中断或 SSHD 卡死时，`exit_status_ready()` 永远返回 False，循环无限空转，`remote_exec` 永久卡住。

**修复**：在轮询循环中加入 `deadline = time.time() + timeout` 时间追踪，超时后主动 `chan.close()` 并返回超时错误信息。

**涉及文件**：`ssh_manager.py` 的 `execute()` 方法（第 196-237 行）

## 插件依赖自动补齐

`plugin.yaml` 声明 `pip_dependencies: [paramiko]`，`register()` 入口自动检测并安装：

1. 插件加载时检测 `import paramiko`
2. 缺则自动 `pip install paramiko`
3. 装成功才注册工具，失败则跳过并打日志

主会话和子代理共用同一份自动补齐逻辑。
