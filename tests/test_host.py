import pytest

from losslens.cli import _run_root


def test_run_root_defaults_to_the_copy(monkeypatch, tmp_path):
    monkeypatch.delenv("LOSSLENS_MT4_HOST", raising=False)
    monkeypatch.setenv("LOSSLENS_DATA", str(tmp_path))

    assert _run_root() == tmp_path / "mt4" / "terminal"


def test_run_root_uses_the_logged_in_host(monkeypatch, tmp_path):
    host = tmp_path / "host"
    host.mkdir()
    (host / "terminal.exe").write_bytes(b"terminal")
    monkeypatch.setenv("LOSSLENS_MT4_HOST", str(host))

    assert _run_root() == host


def test_run_root_refuses_a_host_without_terminal(monkeypatch, tmp_path):
    host = tmp_path / "host"
    host.mkdir()
    monkeypatch.setenv("LOSSLENS_MT4_HOST", str(host))

    with pytest.raises(FileNotFoundError, match="terminal.exe"):
        _run_root()
