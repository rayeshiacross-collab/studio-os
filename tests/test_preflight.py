"""Host readiness failures are tested without contacting or starting a renderer."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from urllib.error import URLError
import subprocess

from studio_os import preflight as check


class PreflightTests(TestCase):
    def test_renderer_client_ignores_inherited_proxy(self):
        import asyncio
        from studio_os.engines.wan22 import Wan22Engine
        with patch.dict("os.environ", {"ALL_PROXY": "socks5h://127.0.0.1:1", "HTTPS_PROXY": "http://127.0.0.1:1"}):
            engine = Wan22Engine()
            try:
                self.assertFalse(engine.client._trust_env)
                self.assertFalse(engine.client.follow_redirects)
            finally:
                asyncio.run(engine.close())

    def test_missing_required_dependency_stops_before_network(self):
        with patch.object(check.shutil, "which", return_value=None), patch.object(check, "fetch_json") as fetch:
            with self.assertRaisesRegex(RuntimeError, "ffmpeg"):
                check.run_checks("http://localhost:8188")
            fetch.assert_not_called()

    def test_unknown_node_and_missing_weights_rejected(self):
        graph = {"1": {"class_type": "Loader", "inputs": {"unet_name": "wanted.safetensors"}}}
        for inventory in ({}, {"Loader": {"input": {"required": {"unet_name": [["other.safetensors"]]}}}}):
            with self.assertRaises(ValueError):
                check.workflow_inventory(graph, inventory)
        check.workflow_inventory(graph, {"Loader": {"input": {"required": {"unet_name": [["wanted.safetensors"]]}}}})

    def test_prerequisites_do_not_certify_render(self):
        with TemporaryDirectory() as directory:
            graph = Path(directory) / "workflow.json"
            graph.write_text(json.dumps({"1": {"class_type": "Fixture", "inputs": {}}}))
            with patch.object(check.shutil, "which", return_value="/fixture/bin"), patch.object(check.compileall, "compile_dir", return_value=True), patch.object(check.subprocess, "run") as run, patch.object(check, "fetch_json", side_effect=[{"system": {}, "devices": [{}]}, {"Fixture": {}}]) as fetch:
                result = check.run_checks("http://localhost:8188", native=True, workflow_path=graph)
                self.assertEqual(result["status"], "PREREQUISITES_VERIFIED")
                self.assertFalse(result["render_verified"])
                self.assertFalse(result["production_ready"])
                self.assertEqual(fetch.call_count, 2)
                self.assertFalse(any("docker" in call.args[0] for call in run.call_args_list))

    def test_compose_error_stops_before_network(self):
        with patch.object(check.shutil, "which", return_value="/fixture/bin"), patch.object(check.compileall, "compile_dir", return_value=True), patch.object(check.subprocess, "run", side_effect=[None, None, None, subprocess.CalledProcessError(1, ["docker"])]), patch.object(check, "fetch_json") as fetch:
            with self.assertRaises(subprocess.CalledProcessError):
                check.run_checks("http://localhost:8188")
            fetch.assert_not_called()

    def test_unavailable_renderer_and_malformed_inventory_fail(self):
        for response in (URLError("offline"), {}, {"system": {}, "devices": []}):
            with patch.object(check.shutil, "which", return_value="/fixture/bin"), patch.object(check.compileall, "compile_dir", return_value=True), patch.object(check.subprocess, "run"), patch.object(check, "fetch_json", side_effect=response if isinstance(response, Exception) else [response]):
                with self.assertRaises((URLError, ValueError)):
                    check.run_checks("http://localhost:8188")

    def test_credentials_fragments_and_redirects_rejected(self):
        for url in ("http://secret@localhost:8188", "file:///tmp/stats", "http://localhost:8188/#x", "http://localhost:8188/?token=x", "http://localhost/\n"):
            with self.assertRaises(ValueError):
                check.renderer_url(url)
        with self.assertRaises(ValueError):
            check.NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.test")
