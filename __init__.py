"""Remote SSH plugin — register tools for managing SSH connections to remote servers."""
from __future__ import annotations

import logging
import subprocess
import sys

from . import schemas, tools

logger = logging.getLogger(__name__)


def _ensure_dependencies() -> bool:
    """Auto-install paramiko if missing."""
    try:
        import paramiko  # noqa: F401
        return True
    except ImportError:
        pass

    logger.warning("[remote-ssh] paramiko not found — attempting auto-install...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "paramiko"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            logger.info("[remote-ssh] paramiko installed successfully")
            # re-import to verify
            import paramiko  # noqa: F401
            return True
        else:
            logger.error(
                "[remote-ssh] pip install paramiko failed:\n%s",
                result.stderr or result.stdout,
            )
    except Exception as e:
        logger.error("[remote-ssh] auto-install paramiko failed: %s", e)

    logger.error(
        "[remote-ssh] paramiko is required. Install manually: "
        "%s -m pip install paramiko",
        sys.executable,
    )
    return False


def register(ctx) -> None:
    """Register all remote-ssh tools. Called once by the plugin loader at startup."""
    if not _ensure_dependencies():
        logger.error("[remote-ssh] Plugin cannot load — missing paramiko dependency")
        return

    ctx.register_tool(
        name="remote_connect",
        toolset="remote-ssh",
        schema=schemas.REMOTE_CONNECT,
        handler=tools.remote_connect,
        emoji="🔗",
    )
    ctx.register_tool(
        name="remote_disconnect",
        toolset="remote-ssh",
        schema=schemas.REMOTE_DISCONNECT,
        handler=tools.remote_disconnect,
        emoji="✂️",
    )
    ctx.register_tool(
        name="remote_list",
        toolset="remote-ssh",
        schema=schemas.REMOTE_LIST,
        handler=tools.remote_list,
        emoji="📋",
    )
    ctx.register_tool(
        name="remote_exec",
        toolset="remote-ssh",
        schema=schemas.REMOTE_EXEC,
        handler=tools.remote_exec,
        emoji="▶️",
    )
    ctx.register_tool(
        name="remote_info",
        toolset="remote-ssh",
        schema=schemas.REMOTE_INFO,
        handler=tools.remote_info,
        emoji="ℹ️",
    )
    ctx.register_tool(
        name="remote_health",
        toolset="remote-ssh",
        schema=schemas.REMOTE_HEALTH,
        handler=tools.remote_health,
        emoji="💓",
    )
    ctx.register_tool(
        name="remote_set_cwd",
        toolset="remote-ssh",
        schema=schemas.REMOTE_SET_CWD,
        handler=tools.remote_set_cwd,
        emoji="📁",
    )
    ctx.register_tool(
        name="remote_sudo",
        toolset="remote-ssh",
        schema=schemas.REMOTE_SUDO,
        handler=tools.remote_sudo,
        emoji="🛡️",
    )

    logger.info("[remote-ssh] Registered 8 tools")
