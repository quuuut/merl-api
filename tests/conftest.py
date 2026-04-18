import threading
import time
import pytest
import httpx
import uvicorn

from main import app

BASE_URL = "http://127.0.0.1:8765"


class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="error")
        self.server = uvicorn.Server(self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


@pytest.fixture(scope="session")
def server():
    thread = ServerThread()
    thread.start()

    # Wait until the server ready
    for _ in range(20):
        try:
            httpx.get(f"{BASE_URL}/v1/models", timeout=1)
            break
        except httpx.ConnectError:
            time.sleep(0.25)
    else:
        pytest.fail("Server did not start in time")

    yield BASE_URL

    thread.stop()
    thread.join(timeout=5)


@pytest.fixture
def client(server):
    with httpx.Client(base_url=server, timeout=30) as c:
        yield c


@pytest.fixture
def async_client(server):
    # Used for streaming tests
    return server  # tests construct their own httpx.AsyncClient