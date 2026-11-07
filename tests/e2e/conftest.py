"""Start the app in a background thread for browser tests."""

import socket
import threading
import time
from datetime import date

import pytest
import uvicorn

from strava_predictor.web.app import create_app

REFERENCE_DATE = date(2026, 11, 5)
STARTUP_TIMEOUT_S = 10


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def base_url():
    port = _free_port()
    app = create_app(clock=lambda: REFERENCE_DATE)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("test server did not start")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=STARTUP_TIMEOUT_S)


def pytest_collection_modifyitems(items):
    for item in items:
        if "tests/e2e" in item.nodeid.replace("\\", "/"):
            item.add_marker(pytest.mark.e2e)
