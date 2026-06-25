"""Tool handlers — the code that runs when the LLM calls each remote-ssh tool."""
from __future__ import annotations

import json
from typing import Any

from .ssh_manager import get_manager


def _get_session_id(kwargs: dict) -> str:
    """Extract session_id from handler kwargs, falling back to 'default'."""
    return kwargs.get("session_id") or "default"


# ── remote_connect ───────────────────────────────────────────────

def remote_connect(args: dict, **kwargs) -> str:
    host = str(args.get("host", "")).strip()
    if not host:
        return json.dumps({"error": "host 参数必填"}, ensure_ascii=False)

    port = int(args.get("port", 22))
    username = str(args.get("username", "root")).strip() or "root"
    password = str(args.get("password", ""))
    key_path = str(args.get("key_path", ""))
    passphrase = str(args.get("passphrase", ""))

    if not password and not key_path:
        return json.dumps({"error": "需要提供 password 或 key_path"}, ensure_ascii=False)

    session_id = _get_session_id(kwargs)
    mgr = get_manager()

    try:
        info = mgr.connect(
            session_id=session_id,
            host=host,
            port=port,
            username=username,
            password=password,
            key_path=key_path,
            passphrase=passphrase,
        )
        return json.dumps({"success": True, "connection": info}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ── remote_disconnect ────────────────────────────────────────────

def remote_disconnect(args: dict, **kwargs) -> str:
    session_id = _get_session_id(kwargs)
    mgr = get_manager()
    ok = mgr.disconnect(session_id)
    return json.dumps({"disconnected": ok}, ensure_ascii=False)


# ── remote_list ──────────────────────────────────────────────────

def remote_list(args: dict, **kwargs) -> str:
    session_id = _get_session_id(kwargs)
    mgr = get_manager()
    conn = mgr.get_connection(session_id)
    if conn is None:
        return json.dumps({"connected": False, "message": "当前会话没有活跃的 SSH 连接"}, ensure_ascii=False)
    return json.dumps({"connected": True, "connection": conn.to_dict()}, ensure_ascii=False)


# ── remote_exec ──────────────────────────────────────────────────

def remote_exec(args: dict, **kwargs) -> str:
    command = str(args.get("command", "")).strip()
    if not command:
        return json.dumps({"error": "command 参数必填"}, ensure_ascii=False)

    timeout = float(args.get("timeout", 60))
    cwd = str(args.get("cwd", ""))

    session_id = _get_session_id(kwargs)
    mgr = get_manager()

    rc, stdout, stderr = mgr.execute(
        session_id=session_id,
        command=command,
        timeout=timeout,
        cwd=cwd,
    )

    result = {
        "exit_code": rc,
        "stdout": stdout,
    }
    if stderr:
        result["stderr"] = stderr

    return json.dumps(result, ensure_ascii=False)


# ── remote_info ──────────────────────────────────────────────────

def remote_info(args: dict, **kwargs) -> str:
    force = bool(args.get("force", False))
    session_id = _get_session_id(kwargs)
    mgr = get_manager()

    try:
        info = mgr.detect_env(session_id, force=force)
        return json.dumps(info, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ── remote_health ────────────────────────────────────────────────

def remote_health(args: dict, **kwargs) -> str:
    session_id = _get_session_id(kwargs)
    mgr = get_manager()

    try:
        health = mgr.health_check(session_id)
        return json.dumps(health, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ── remote_set_cwd ───────────────────────────────────────────────

def remote_set_cwd(args: dict, **kwargs) -> str:
    path = str(args.get("path", "")).strip()
    if not path:
        return json.dumps({"error": "path 参数必填"}, ensure_ascii=False)

    session_id = _get_session_id(kwargs)
    mgr = get_manager()

    ok = mgr.set_cwd(session_id, path)
    if ok:
        return json.dumps({"success": True, "cwd": path}, ensure_ascii=False)
    else:
        return json.dumps({"error": f"目录不存在或无法访问: {path}"}, ensure_ascii=False)


# ── remote_sudo ──────────────────────────────────────────────────

def remote_sudo(args: dict, **kwargs) -> str:
    command = str(args.get("command", "")).strip()
    if not command:
        return json.dumps({"error": "command 参数必填"}, ensure_ascii=False)

    password = str(args.get("password", ""))
    timeout = float(args.get("timeout", 60))

    session_id = _get_session_id(kwargs)
    mgr = get_manager()

    # set sudo password if provided
    if password:
        ok = mgr.set_sudo_password(session_id, password)
        if not ok:
            return json.dumps({"error": "无活跃连接，无法设置 sudo 密码"}, ensure_ascii=False)

    rc, stdout, stderr = mgr.execute(
        session_id=session_id,
        command=command,
        timeout=timeout,
        sudo=True,
    )

    result = {
        "exit_code": rc,
        "stdout": stdout,
    }
    if stderr:
        result["stderr"] = stderr

    return json.dumps(result, ensure_ascii=False)
