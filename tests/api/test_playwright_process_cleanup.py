from __future__ import annotations

import signal
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import browser_capture_smoke as pw  # noqa: E402


def test_run_command_with_timeout_kills_process_group(monkeypatch: pytest.MonkeyPatch) -> None:
    opened_kwargs: dict[str, object] = {}
    sent_signals: list[int] = []

    class FakeProcess:
        pid = 4242
        returncode: int | None = None

        def __init__(self, command: list[str], **kwargs: object) -> None:
            self.command = command
            self.communicate_calls = 0
            opened_kwargs.update(kwargs)

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise subprocess.TimeoutExpired(self.command, timeout)
            return "captured stdout", "captured stderr"

        def poll(self) -> int | None:
            return self.returncode

        def wait(self, timeout: float | None = None) -> int:
            if len(sent_signals) == 1:
                raise subprocess.TimeoutExpired(self.command, timeout)
            self.returncode = -signal.SIGKILL
            return self.returncode

    monkeypatch.setattr(pw.subprocess, "Popen", FakeProcess)
    monkeypatch.setattr(pw.os, "killpg", lambda pid, sig: sent_signals.append(sig))

    with pytest.raises(subprocess.TimeoutExpired) as error_info:
        pw.run_command_with_timeout(["fake-pwcli"], timeout_seconds=0.01)

    assert opened_kwargs["start_new_session"] is True
    assert sent_signals == [signal.SIGTERM, signal.SIGKILL]
    assert error_info.value.stdout == "captured stdout"
    assert error_info.value.stderr == "captured stderr"


def test_close_session_quietly_removes_socket_after_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    socket_path = tmp_path / "pw-test" / "cli" / "daemon-atlas.sock"
    socket_path.parent.mkdir(parents=True)
    socket_path.write_text("", encoding="utf-8")
    killed_sessions: list[str] = []

    def timeout_close(*_args: object, **_kwargs: object) -> str:
        raise subprocess.TimeoutExpired(["pwcli", "close"], 5)

    monkeypatch.setattr(pw.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(pw, "run_pwcli", timeout_close)
    monkeypatch.setattr(pw, "kill_session_cli_daemons", lambda session: killed_sessions.append(session))

    pw.close_session_quietly("atlas")

    assert killed_sessions == ["atlas"]
    assert not socket_path.exists()
