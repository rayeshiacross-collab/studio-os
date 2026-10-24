"""Exercise the smoke checker over HTTP, including HTTPError response bodies."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def health_server(status, body):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            assert self.path == '/health'
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/health'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def check(status, body, expected='unreachable'):
    with health_server(status, body) as url:
        return subprocess.run(
            [sys.executable, str(ROOT / 'scripts/check_api_smoke.py'),
             '--url', url, '--expect-comfyui', expected, '--attempts', '1'],
            capture_output=True, text=True, timeout=10,
        )


def test_offline_boot_accepts_explicit_degraded_health():
    result = check(503, b'{"detail":{"status":"degraded","comfyui":"unreachable"}}')
    assert result.returncode == 0, result.stderr
    assert 'render_verified=false' in result.stdout


def test_online_check_requires_real_health_contract():
    result = check(200, b'{"status":"ok","comfyui":"reachable"}', 'reachable')
    assert result.returncode == 0, result.stderr


def test_online_check_rejects_unreachable_renderer():
    result = check(503, b'{"detail":{"status":"degraded","comfyui":"unreachable"}}', 'reachable')
    assert result.returncode != 0
    assert 'HTTP 503' in result.stderr


def test_boot_rejects_uninitialized_orchestrator():
    result = check(503, b'{"detail":"Orchestrator not ready"}')
    assert result.returncode != 0
    assert 'Orchestrator not ready' in result.stderr


def test_boot_rejects_invalid_json_and_reports_response():
    result = check(500, b'internal failure')
    assert result.returncode != 0
    assert 'HTTP 500' in result.stderr
    assert 'internal failure' in result.stderr


def test_api_reports_degraded_when_renderer_connection_is_refused():
    import asyncio
    import httpx
    from studio_os.core.orchestrator import Orchestrator
    from studio_os.interfaces import api

    async def request_health():
        original = api.orchestrator
        api.orchestrator = Orchestrator(comfyui_url='http://127.0.0.1:1')
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app),
                                         base_url='http://api') as client:
                response = await client.get('/health')
            assert response.status_code == 503
            assert response.json() == {
                'detail': {'status': 'degraded', 'comfyui': 'unreachable'}
            }
        finally:
            await api.orchestrator.engine.close()
            api.orchestrator = original

    asyncio.run(request_health())
