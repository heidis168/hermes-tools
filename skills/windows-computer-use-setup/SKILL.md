---
name: windows-computer-use-setup
description: Use when setting up Hermes computer_use on Windows 11 — install cua-driver, register MCP, fix pywin32 trap, verify end-to-end.
version: 1.0.0
author: agent
tags: [windows, computer-use, cua-driver, mcp, setup, troubleshooting]
---

# Windows Computer Use 完整配置指南

在 Windows 11 上让 Hermes 的 `computer_use` 工具正常工作，从零到可用。

## When to Use

- 首次在 Windows 上启用 Hermes 桌面控制
- `computer_use` 报 `backend unavailable` / `session never reached ready`
- `hermes computer-use status` 显示正常但工具不可用

## 概述

Hermes 的 `computer_use` 底层由 **cua-driver** 驱动（TryCua 项目），通过 MCP 协议通信。Windows 上使用 **UI Automation (UIA)** 实现后台桌面操控。

核心链路：
```
Hermes agent → cua_backend.py → cua-driver mcp (stdio) → cua-driver serve (daemon) → Windows UIA
```

## 安装步骤

### 1. 安装 cua-driver

```bash
hermes computer-use install
```

安装脚本自动完成：
- 下载 cua-driver-rs 到 `%LOCALAPPDATA%\Programs\Cua\cua-driver\bin\`
- 添加到 Windows 用户 PATH
- 注册开机自启（Scheduled Task, RunLevel=Highest）
- 启动后台服务

验证：

```bash
cua-driver --version          # 应输出 cua-driver 0.6.8
cua-driver health_report      # 全部 pass
cua-driver autostart status   # registered (running)
```

### 2. PATH 修复（git-bash 用户必做）

安装脚本把 cua-driver 加入 **Windows 用户 PATH**，但 git-bash (MSYS) 不会自动加载。如果 `which cua-driver` 返回空：

```bash
echo 'export PATH="$PATH:/c/Users/heidis/AppData/Local/Programs/Cua/cua-driver/bin"' >> ~/.bashrc
source ~/.bashrc
```

### 3. 注册 MCP 服务器

```bash
printf 'Y\n' | hermes mcp add cua-driver \
  --command "C:\Users\heidis\AppData\Local\Programs\Cua\cua-driver\bin\cua-driver.exe" \
  --args mcp
```

验证：

```bash
hermes mcp list
# 应显示: cua-driver  all  ✓ enabled
```

### 4. 增加 MCP 发现超时

默认 1.5 秒太短，cua-driver MCP 初始化需要连接本地 daemon：

```bash
hermes config set mcp_discovery_timeout 15
```

### 5. ⚠️ 关键陷阱：pywin32 缺失

**这是最常见的失败原因。** Hermes 后端进程使用 **uv 管理的系统 Python**（`%APPDATA%\Roaming\uv\python\cpython-3.11-windows-x86_64-none\pythonw.exe`），而不是 Hermes venv。uv Python 不包含 `pywin32`，而 `mcp` 包依赖它。

**症状**：`computer_use` 调用后等 15 秒，报 `cua-driver session never reached ready (timeout 15s)`

**诊断**：

```bash
# 查看 pythonw.exe 路径
powershell -NoProfile -Command "Get-Process pythonw | Select-Object Id, Path"

# 用 uv Python 测试 mcp 导入
"C:/Users/heidis/AppData/Roaming/uv/python/cpython-3.11-windows-x86_64-none/python.exe" \
  -c "import mcp; print(mcp.__version__)"
# 如果报 No module named 'pywintypes'，确认问题
```

**修复**：

```bash
uv pip install pywin32 \
  --python "C:/Users/heidis/AppData/Roaming/uv/python/cpython-3.11-windows-x86_64-none/python.exe" \
  --break-system-packages
```

### 6. 重启 Hermes

以上配置写入后必须重启 Hermes 才会加载 MCP 工具。

## 端到端验证

重启后：

```python
computer_use(action="capture", mode="ax")
```

应返回当前前台窗口的完整 UI 树（按钮、输入框、链接等），包含元素编号。

```python
computer_use(action="list_apps")
```

应返回运行中应用列表。

## 故障排除速查表

| 症状 | 原因 | 解决 |
|---|---|---|
| `cua-driver: not installed` | 二进制未安装 | `hermes computer-use install` |
| `No MCP servers configured` | MCP 未注册 | `printf 'Y\n' \| hermes mcp add cua-driver ...` |
| `session never reached ready (timeout 15s)` | pywin32 缺失 | 步骤 5 |
| `which cua-driver` 返回空 | git-bash PATH 未更新 | 步骤 2 |
| `computer_use` 工具不在列表中 | 未重启 | 重启 Hermes |
| capture 返回空 | 没有前台窗口或 UIA 权限问题 | `cua-driver health_report` |

## 环境信息

- 系统：Windows 11 (10.0.26200)
- Shell：git-bash (MSYS)
- Python：uv 管理 Python 3.11.15（系统）+ Hermes venv Python 3.11（项目）
- cua-driver：0.6.8 (x86_64-pc-windows-msvc)
- mcp：1.26.0
- pywin32：312
