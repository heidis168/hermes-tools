---
name: computer-use-setup
description: Use when setting up or troubleshooting Hermes computer_use on any platform — install cua-driver, register MCP, diagnose failures, verify end-to-end. Covers Windows, Linux, and macOS.
version: 1.0.0
author: agent
tags: [computer-use, cua-driver, mcp, setup, troubleshooting, cross-platform]
---

# Computer Use 配置指南

在任意平台上让 Hermes 的 `computer_use` 工具正常工作，从零到可用。

## When to Use

- 首次启用 Hermes 桌面控制
- `computer_use` 报 `backend unavailable` / `session never reached ready`
- `hermes computer-use status` 显示正常但工具不可用
- 任何平台（Windows / Linux / macOS）的 computer-use 故障

## 概述

Hermes 的 `computer_use` 底层由 **cua-driver** 驱动（TryCua 项目），通过 MCP 协议通信。平台可访问性层：

| 平台 | 底层技术 |
|------|---------|
| Windows | UI Automation (UIA) |
| Linux | AT-SPI (X11 / Wayland via XWayland) |
| macOS | Accessibility API (AX) |

核心链路：
```
Hermes agent → cua_backend.py → cua-driver mcp (stdio) → cua-driver serve (daemon) → 平台可访问性层
```

## 通用安装步骤（所有平台）

### 1. 安装 cua-driver

```bash
hermes computer-use install
```

安装脚本自动完成：下载二进制 → 添加到 PATH → 注册开机自启 → 启动后台服务。

验证：

```bash
cua-driver --version
cua-driver health_report
cua-driver autostart status    # 应显示 registered (running)
```

### 2. 注册 MCP 服务器

```bash
printf 'Y\n' | hermes mcp add cua-driver \
  --command "<cua-driver 完整路径>" \
  --args mcp
```

验证：

```bash
hermes mcp list
# 应显示: cua-driver  all  ✓ enabled
```

### 3. 增加 MCP 发现超时

默认 1.5 秒太短，cua-driver MCP 初始化需要连接本地 daemon：

```bash
hermes config set mcp_discovery_timeout 15
```

### 4. 重启 Hermes

以上配置写入后必须重启才会加载 MCP 工具。

---

## 平台特定配置

### Windows

#### PATH 修复（git-bash / MSYS 用户）

安装脚本把 cua-driver 加入 **Windows 用户 PATH**，但 git-bash 不会自动加载：

```bash
# 检查
which cua-driver

# 修复
echo 'export PATH="$PATH:/c/Users/<user>/AppData/Local/Programs/Cua/cua-driver/bin"' >> ~/.bashrc
source ~/.bashrc
```

#### ⚠️ pywin32 缺失陷阱

**Windows 上最常见的失败原因。** Hermes 后端进程使用 **uv 管理的系统 Python**，不是 Hermes venv。uv Python 不包含 `pywin32`（`mcp` 包的传递依赖）。

**症状**：`computer_use` 调用后等 15 秒，报 `cua-driver session never reached ready (timeout 15s)`

**诊断**：

```bash
# 查看后端 Python 路径
powershell -NoProfile -Command "Get-Process pythonw | Select-Object Id, Path"

# 测试 mcp 导入
"<uv Python 路径>" -c "import mcp; print(mcp.__version__)"
# 如果报 No module named 'pywintypes'，确认问题
```

**修复**：

```bash
uv pip install pywin32 \
  --python "<uv Python 路径>" \
  --break-system-packages
```

uv Python 路径通常是：
```
C:\Users\<user>\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe
```

### Linux

> 待补充 — 遇到 Linux 配置经验后追加此章节。

预期关注点：
- DISPLAY 环境变量（X11）
- Wayland / XWayland 兼容性
- AT-SPI 权限
- `hermes computer-use doctor` 诊断

### macOS

> 待补充 — 遇到 macOS 配置经验后追加此章节。

预期关注点：
- Accessibility 权限（系统设置 → 隐私与安全性 → 辅助功能）
- Screen Recording 权限
- TCC 授权流程

---

## 端到端验证

重启 Hermes 后：

```python
# 获取当前窗口 UI 树（文本模式，不截图）
computer_use(action="capture", mode="ax")

# 列出运行中的应用
computer_use(action="list_apps")

# 带截图的完整捕获
computer_use(action="capture", mode="som")
```

`capture(mode="ax")` 应返回当前前台窗口的完整 UI 树（按钮、输入框、链接等），包含元素编号。

---

## 故障排除速查表

| 症状 | 原因 | 解决 |
|------|------|------|
| `cua-driver: not installed` | 二进制未安装 | `hermes computer-use install` |
| `No MCP servers configured` | MCP 未注册 | `printf 'Y\n' \| hermes mcp add cua-driver ...` |
| `session never reached ready (timeout 15s)` | 传递依赖缺失（Windows: pywin32） | 见平台章节 |
| `which cua-driver` 返回空 | PATH 未更新 | 见平台章节 |
| `computer_use` 工具不在列表中 | 未重启 | 重启 Hermes |
| capture 返回空 | 无前台窗口或权限问题 | `cua-driver health_report` |
