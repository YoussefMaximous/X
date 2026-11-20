import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture(scope="session", autouse=True)
def block_network():
    def blocked(*args, **kwargs):
        raise RuntimeError("network is blocked in tests")

    patcher = pytest.MonkeyPatch()
    patcher.setattr(socket.socket, "connect", blocked)
    patcher.setattr(socket.socket, "connect_ex", blocked)
    patcher.setattr(socket, "create_connection", blocked)
    patcher.setattr(socket, "getaddrinfo", blocked)
    yield
    patcher.undo()
