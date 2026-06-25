"""SSH connection manager — session-scoped, thread-safe, with heartbeat and sudo caching."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SSHConnection:
    client: Any  # paramiko.SSHClient
    host: str
    port: int
    username: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    default_cwd: str = "/"
    sudo_password: str = ""
    sudo_verified: bool = False
    sudo_verified_at: datetime | None = None
    # cached env info
    hostname: str = ""
    remote_os: str = ""
    remote_kernel: str = ""
    remote_arch: str = ""
    remote_shell: str = ""
    cpu_info: str = ""
    mem_info: str = ""
    disk_info: str = ""
    tools_available: dict[str, bool] = field(default_factory=dict)
    env_detected_at: datetime | None = None
    # health
    consecutive_failures: int = 0
    last_error: str = ""
    last_health_check: datetime | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "connected_at": self.connected_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "default_cwd": self.default_cwd,
            "hostname": self.hostname,
            "remote_os": self.remote_os,
            "remote_kernel": self.remote_kernel,
            "uptime_seconds": (datetime.now(timezone.utc) - self.connected_at).total_seconds(),
            "latency_ms": self.latency_ms,
            "consecutive_failures": self.consecutive_failures,
        }


class SSHManager:
    """Singleton — one SSH connection per session_id."""

    _instance: SSHManager | None = None
    _lock = threading.Lock()

    def __new__(cls) -> SSHManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: dict[str, SSHConnection] = {}
            cls._instance._reconnect_params: dict[str, dict] = {}
        return cls._instance

    # ── connect / disconnect ──────────────────────────────────────

    def connect(
        self,
        session_id: str,
        host: str,
        port: int = 22,
        username: str = "root",
        password: str = "",
        key_path: str = "",
        passphrase: str = "",
    ) -> dict:
        import paramiko

        if not host:
            raise ValueError("host is required")

        with self._lock:
            # disconnect existing
            old = self._connections.pop(session_id, None)
            self._reconnect_params.pop(session_id, None)
        if old:
            try:
                old.client.close()
            except Exception:
                pass

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict = {
            "hostname": host,
            "port": port,
            "username": username,
            "timeout": 15,
            "allow_agent": False,
            "look_for_keys": False,
        }
        if password:
            connect_kwargs["password"] = password
        if key_path:
            connect_kwargs["key_filename"] = key_path
        if passphrase:
            connect_kwargs["passphrase"] = passphrase

        try:
            client.connect(**connect_kwargs)
        except paramiko.AuthenticationException as e:
            raise ConnectionError(f"认证失败 {username}@{host}:{port} — {e}") from e
        except (OSError, Exception) as e:
            raise ConnectionError(f"无法连接 {host}:{port} — {e}") from e

        conn = SSHConnection(
            client=client,
            host=host,
            port=port,
            username=username,
        )

        with self._lock:
            self._connections[session_id] = conn
            self._reconnect_params[session_id] = {
                "host": host, "port": port, "username": username,
                "password": password, "key_path": key_path, "passphrase": passphrase,
            }

        logger.info("[remote-ssh] Connected %s@%s:%d (session=%s)", username, host, port, session_id)
        return conn.to_dict()

    def disconnect(self, session_id: str) -> bool:
        with self._lock:
            conn = self._connections.pop(session_id, None)
            self._reconnect_params.pop(session_id, None)
        if conn is None:
            return False
        try:
            conn.client.close()
        except Exception:
            pass
        logger.info("[remote-ssh] Disconnected %s@%s:%d", conn.username, conn.host, conn.port)
        return True

    def reconnect(self, session_id: str) -> dict:
        with self._lock:
            params = self._reconnect_params.get(session_id)
        if not params:
            raise ValueError("没有缓存的连接参数，请用 remote_connect 重新连接")
        return self.connect(session_id, **params)

    def get_connection(self, session_id: str) -> SSHConnection | None:
        with self._lock:
            return self._connections.get(session_id)

    # ── command execution ─────────────────────────────────────────

    def execute(
        self,
        session_id: str,
        command: str,
        timeout: float = 60,
        cwd: str = "",
        sudo: bool = False,
    ) -> tuple[int, str, str]:
        conn = self.get_connection(session_id)
        if conn is None:
            return -1, "", "错误: 当前会话没有活跃的 SSH 连接。请先用 remote_connect 连接。"

        client = conn.client

        # build command
        effective_cwd = cwd or conn.default_cwd
        parts = []
        if effective_cwd and effective_cwd != "/":
            parts.append(f"cd {effective_cwd}")
        if sudo:
            if not conn.sudo_verified:
                # warm sudo cache
                self._warm_sudo(conn)
            parts.append(f"sudo {command}")
        else:
            parts.append(command)
        full_cmd = " && ".join(parts) if len(parts) > 1 else parts[0]

        try:
            chan = client.get_transport().open_session()
            chan.settimeout(timeout)
            chan.exec_command(full_cmd)

            stdout = b""
            stderr = b""
            deadline = time.time() + timeout
            while True:
                if time.time() > deadline:
                    chan.close()
                    conn.consecutive_failures += 1
                    conn.last_error = f"命令执行超时 ({timeout}s)"
                    return -1, "", f"SSH 执行超时 ({timeout}s): {full_cmd[:200]}"

                if chan.recv_ready():
                    stdout += chan.recv(4096)
                if chan.recv_stderr_ready():
                    stderr += chan.recv_stderr(4096)
                if chan.exit_status_ready():
                    break
                time.sleep(0.05)

            # drain remaining
            while chan.recv_ready():
                stdout += chan.recv(4096)
            while chan.recv_stderr_ready():
                stderr += chan.recv_stderr(4096)

            rc = chan.recv_exit_status()
            chan.close()

            conn.last_used = datetime.now(timezone.utc)
            conn.consecutive_failures = 0
            conn.last_error = ""

            return rc, stdout.decode(errors="replace"), stderr.decode(errors="replace")

        except Exception as e:
            conn.consecutive_failures += 1
            conn.last_error = str(e)
            return -1, "", f"SSH 执行失败: {e}"

    # ── sudo ──────────────────────────────────────────────────────

    def _warm_sudo(self, conn: SSHConnection) -> bool:
        if not conn.sudo_password:
            return False
        try:
            rc, out, err = self._raw_exec(conn, f"echo '{conn.sudo_password}' | sudo -S -v 2>&1 && sudo -n true")
            if rc == 0:
                conn.sudo_verified = True
                conn.sudo_verified_at = datetime.now(timezone.utc)
                return True
        except Exception:
            pass
        return False

    def set_sudo_password(self, session_id: str, password: str) -> bool:
        conn = self.get_connection(session_id)
        if conn is None:
            return False
        conn.sudo_password = password
        return self._warm_sudo(conn)

    def _raw_exec(self, conn: SSHConnection, cmd: str, timeout: float = 30) -> tuple[int, str, str]:
        chan = conn.client.get_transport().open_session()
        chan.settimeout(timeout)
        chan.exec_command(cmd)
        out = chan.recv(65536).decode(errors="replace")
        err = chan.recv_stderr(65536).decode(errors="replace")
        rc = chan.recv_exit_status()
        chan.close()
        return rc, out, err

    # ── health check ──────────────────────────────────────────────

    def health_check(self, session_id: str) -> dict:
        conn = self.get_connection(session_id)
        if conn is None:
            return {"connected": False, "status": "disconnected", "error": "无活跃连接"}

        start = time.time()
        try:
            rc, out, _ = self._raw_exec(conn, "echo OK", timeout=10)
            latency = (time.time() - start) * 1000
            conn.latency_ms = round(latency, 1)
            conn.last_health_check = datetime.now(timezone.utc)

            if rc == 0 and "OK" in out:
                conn.consecutive_failures = 0
                return {
                    "connected": True,
                    "status": "healthy",
                    "latency_ms": conn.latency_ms,
                    "consecutive_failures": 0,
                }
            else:
                conn.consecutive_failures += 1
                return {
                    "connected": True,
                    "status": "degraded" if conn.consecutive_failures < 3 else "unstable",
                    "latency_ms": conn.latency_ms,
                    "consecutive_failures": conn.consecutive_failures,
                    "error": f"exit={rc}, output={out[:200]}",
                }
        except Exception as e:
            conn.consecutive_failures += 1
            conn.last_error = str(e)
            return {
                "connected": False,
                "status": "stale",
                "latency_ms": None,
                "consecutive_failures": conn.consecutive_failures,
                "error": str(e),
            }

    # ── env detection ─────────────────────────────────────────────

    def detect_env(self, session_id: str, force: bool = False) -> dict:
        conn = self.get_connection(session_id)
        if conn is None:
            return {"error": "无活跃连接"}

        if conn.env_detected_at and not force:
            return {
                "hostname": conn.hostname,
                "remote_os": conn.remote_os,
                "remote_kernel": conn.remote_kernel,
                "remote_arch": conn.remote_arch,
                "remote_shell": conn.remote_shell,
                "cpu_info": conn.cpu_info,
                "mem_info": conn.mem_info,
                "disk_info": conn.disk_info,
                "tools_available": conn.tools_available,
                "cached": True,
                "detected_at": conn.env_detected_at.isoformat() if conn.env_detected_at else None,
            }

        probes = {
            "hostname": "hostname",
            "os": "cat /etc/os-release 2>/dev/null | head -3",
            "kernel": "uname -r",
            "arch": "uname -m",
            "shell": "basename $SHELL",
            "cpu": "grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2",
            "mem": "free -h | grep '^Mem:'",
            "disk": "df -h / | tail -1",
            "tools": "for t in git python3 python pip node npm docker kubectl systemctl; do which $t >/dev/null 2>&1 && echo \"$t=yes\" || echo \"$t=no\"; done",
        }

        results = {}
        for key, cmd in probes.items():
            rc, out, _ = self._raw_exec(conn, cmd)
            results[key] = out.strip()

        conn.hostname = results.get("hostname", "")
        conn.remote_os = results.get("os", "").replace("\n", " | ")
        conn.remote_kernel = results.get("kernel", "")
        conn.remote_arch = results.get("arch", "")
        conn.remote_shell = results.get("shell", "")
        conn.cpu_info = results.get("cpu", "").strip()
        conn.mem_info = results.get("mem", "")
        conn.disk_info = results.get("disk", "")

        tools_map = {}
        for line in results.get("tools", "").split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                tools_map[k.strip()] = v.strip() == "yes"
        conn.tools_available = tools_map
        conn.env_detected_at = datetime.now(timezone.utc)

        return {
            "hostname": conn.hostname,
            "remote_os": conn.remote_os,
            "remote_kernel": conn.remote_kernel,
            "remote_arch": conn.remote_arch,
            "remote_shell": conn.remote_shell,
            "cpu_info": conn.cpu_info,
            "mem_info": conn.mem_info,
            "disk_info": conn.disk_info,
            "tools_available": conn.tools_available,
            "cached": False,
            "detected_at": conn.env_detected_at.isoformat(),
        }

    # ── cwd ───────────────────────────────────────────────────────

    def set_cwd(self, session_id: str, path: str) -> bool:
        conn = self.get_connection(session_id)
        if conn is None:
            return False
        # verify path exists
        rc, _, _ = self._raw_exec(conn, f"test -d {path} && echo OK")
        if rc != 0:
            return False
        conn.default_cwd = path
        return True

    # ── close all ─────────────────────────────────────────────────

    def close_all(self):
        with self._lock:
            sessions = list(self._connections.keys())
        for sid in sessions:
            self.disconnect(sid)


# singleton accessor
def get_manager() -> SSHManager:
    return SSHManager()
