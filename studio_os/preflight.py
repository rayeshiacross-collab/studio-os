"""Read-only host checks. Never starts services or submits a render."""
import argparse
import compileall
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
MAX_RESPONSE = 8_000_000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Renderer redirects are not accepted")


def renderer_url(value):
    if not isinstance(value, str) or any(ord(c) < 33 for c in value) or "\\" in value:
        raise ValueError("Invalid renderer URL")
    url = urlsplit(value)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("Renderer URL must be an explicit HTTP(S) endpoint without credentials")
    url.port  # Validate malformed ports before making any request.
    return value.rstrip("/")


def fetch_json(base, path):
    # Host diagnostics must not send local renderer requests to an inherited proxy.
    client = build_opener(ProxyHandler({}), NoRedirect())
    with client.open(base + path, timeout=8) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Renderer response exceeds limit")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("Renderer response must be a JSON object")
    return result


def workflow_inventory(workflow, inventory):
    """Check the configured graph's node classes and advertised model filenames."""
    if not isinstance(workflow, dict) or not workflow:
        raise ValueError("Workflow is empty or invalid")
    models = {"unet_name", "clip_name", "vae_name", "lora_name", "ckpt_name"}
    for node_id, node in workflow.items():
        kind = node["class_type"]
        if kind not in inventory:
            raise ValueError(f"Workflow node {node_id}: missing renderer class {kind}")
        spec = inventory[kind].get("input", {})
        fields = {**spec.get("required", {}), **spec.get("optional", {})}
        for name, value in node.get("inputs", {}).items():
            if name in models and isinstance(value, str):
                declared = fields.get(name, [])
                choices = declared[0] if declared else None
                if not isinstance(choices, list) or value not in choices:
                    raise ValueError(f"Workflow node {node_id}: unavailable model {value}")


def run_checks(base, native=False, workflow_path=None):
    base = renderer_url(base)
    for binary in ("ffmpeg", "ffprobe") + (() if native else ("docker",)):
        if not shutil.which(binary):
            raise RuntimeError(f"Required dependency missing: {binary}")
    if not compileall.compile_dir(ROOT / "studio_os", quiet=2):
        raise RuntimeError("Python compilation failed")
    commands = [[sys.executable, "-m", "pip", "check"], ["ffmpeg", "-version"], ["ffprobe", "-version"]]
    if not native:
        commands.append(["docker", "compose", "config", "--quiet"])
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    stats = fetch_json(base, "/system_stats")
    if not isinstance(stats.get("system"), dict) or not isinstance(stats.get("devices"), list) or not stats["devices"]:
        raise ValueError("Renderer system_stats lacks system/device inventory")
    inventory = fetch_json(base, "/object_info")
    path = Path(workflow_path) if workflow_path else ROOT / "workflows/wan22_character_locked_t2v.json"
    workflow_inventory(json.loads(path.read_text()), inventory)
    return {"status": "PREREQUISITES_VERIFIED", "deployment": "native" if native else "compose",
            "workflow": str(path), "render_verified": False, "production_ready": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true", help="Explicitly check a non-Docker installation")
    parser.add_argument("--workflow", type=Path, help="Actual workflow to check against renderer inventory")
    args = parser.parse_args()
    try:
        result = run_checks(os.environ.get("COMFYUI_URL", "http://localhost:8188"), args.native, args.workflow)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        # Avoid printing endpoint credentials or response bodies into shared logs.
        print(f"FAIL: host prerequisites not verified ({type(exc).__name__})", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
