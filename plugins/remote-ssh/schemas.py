"""Tool schemas — what the LLM sees to decide when to call each tool."""

REMOTE_CONNECT = {
    "name": "remote_connect",
    "description": (
        "通过 SSH 连接到远程服务器。连接后，本会话内可以使用 remote_exec、remote_sudo 等工具在远程执行命令。"
        "支持密码认证和 SSH 私钥认证。同一会话只能保持一个活跃连接，新连接会自动断开旧连接。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "远程主机 IP 地址或域名",
            },
            "port": {
                "type": "integer",
                "description": "SSH 端口，默认 22",
            },
            "username": {
                "type": "string",
                "description": "SSH 用户名，默认 root",
            },
            "password": {
                "type": "string",
                "description": "SSH 密码（与 key_path 二选一）",
            },
            "key_path": {
                "type": "string",
                "description": "SSH 私钥文件路径（与 password 二选一）",
            },
            "passphrase": {
                "type": "string",
                "description": "私钥密码（如果有）",
            },
        },
        "required": ["host"],
    },
}

REMOTE_DISCONNECT = {
    "name": "remote_disconnect",
    "description": "断开当前会话的 SSH 连接。",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

REMOTE_LIST = {
    "name": "remote_list",
    "description": "查看当前会话的 SSH 连接状态。",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

REMOTE_EXEC = {
    "name": "remote_exec",
    "description": (
        "在远程服务器上执行一条命令。需要先用 remote_connect 建立连接。"
        "返回命令的标准输出、标准错误和退出码。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要在远程执行的命令",
            },
            "timeout": {
                "type": "number",
                "description": "超时秒数，默认 60",
            },
            "cwd": {
                "type": "string",
                "description": "工作目录，留空则使用默认远程工作目录",
            },
        },
        "required": ["command"],
    },
}

REMOTE_INFO = {
    "name": "remote_info",
    "description": (
        "获取远程服务器的详细信息：操作系统、内核版本、架构、CPU、内存、磁盘、"
        "已安装的开发工具（git、python、node、docker 等）。首次调用会探测并缓存，"
        "后续调用返回缓存结果。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "force": {
                "type": "boolean",
                "description": "是否强制刷新缓存，默认 false",
            },
        },
    },
}

REMOTE_HEALTH = {
    "name": "remote_health",
    "description": (
        "检查当前 SSH 连接的健康状态：是否连通、延迟、连续失败次数。"
        "用于判断连接是否仍然可用。"
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

REMOTE_SET_CWD = {
    "name": "remote_set_cwd",
    "description": (
        "设置当前会话的默认远程工作目录。设置后，所有 remote_exec 命令（未指定 cwd 时）"
        "将在此目录下执行。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "远程目录的绝对路径",
            },
        },
        "required": ["path"],
    },
}

REMOTE_SUDO = {
    "name": "remote_sudo",
    "description": (
        "在远程服务器上以 sudo 权限执行命令。需要先设置 sudo 密码（通过 password 参数）。"
        "首次调用会验证并缓存 sudo 凭证。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要以 sudo 执行的命令",
            },
            "password": {
                "type": "string",
                "description": "sudo 密码（首次调用或密码变更时需要）",
            },
            "timeout": {
                "type": "number",
                "description": "超时秒数，默认 60",
            },
        },
        "required": ["command"],
    },
}
