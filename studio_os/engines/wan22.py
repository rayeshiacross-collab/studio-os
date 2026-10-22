"""
Open-source video generation engine using ComfyUI + Wan 2.2.

All generation is local and free. Character consistency is enforced
via CanonicalCharacter conditioning (LoRAs + reference images).

Workflow template: workflows/wan22_character_locked_t2v.json
"""

from pathlib import Path
from typing import Dict, Optional
import asyncio
import json
import uuid
import httpx

class Wan22Engine:
    """
    Drives ComfyUI workflows for Wan 2.2 video generation.
    Assumes ComfyUI is running (locally or in Docker) with Wan 2.2 models loaded.
    """

    def __init__(self, comfyui_url: str = "http://localhost:8188"):
        self.comfyui_url = comfyui_url.rstrip("/")
        self.workflow_template = Path(__file__).parent.parent.parent / "workflows" / "wan22_character_locked_t2v.json"
        self.client = httpx.AsyncClient(timeout=300.0)

    async def generate_clip(
        self,
        prompt: str,
        character_conditioning: Optional[Dict] = None,
        duration_seconds: float = 5.0,
        output_path: Path = None,
        seed: Optional[int] = None,
    ) -> Path:
        """Generate a short video clip with optional strict character lock."""
        if output_path is None:
            output_path = Path(f"./renders/{uuid.uuid4()}.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        workflow = self._build_wan22_workflow(
            prompt=prompt,
            conditioning=character_conditioning or {},
            duration=duration_seconds,
            seed=seed or 42,
        )

        # Submit to ComfyUI
        payload = {"prompt": workflow}
        resp = await self.client.post(f"{self.comfyui_url}/prompt", json=payload)
        resp.raise_for_status()
        prompt_id = resp.json()["prompt_id"]

        # Poll for completion
        while True:
            hist = await self.client.get(f"{self.comfyui_url}/history/{prompt_id}")
            hist.raise_for_status()
            data = hist.json()
            if prompt_id in data and "outputs" in data[prompt_id]:
                break
            await asyncio.sleep(2)

        # Download the video (node 13 is SaveVideo)
        outputs = data[prompt_id]["outputs"]
        video_info = None
        for node_out in outputs.values():
            if "videos" in node_out and node_out["videos"]:
                video_info = node_out["videos"][0]
                break
            if "gifs" in node_out and node_out["gifs"]:
                video_info = node_out["gifs"][0]
                break

        if not video_info:
            raise RuntimeError("No video output found in ComfyUI history")

        filename = video_info["filename"]
        subfolder = video_info.get("subfolder", "")
        typ = video_info.get("type", "output")

        view_url = f"{self.comfyui_url}/view?filename={filename}&subfolder={subfolder}&type={typ}"
        vid_resp = await self.client.get(view_url)
        vid_resp.raise_for_status()
        output_path.write_bytes(vid_resp.content)

        return output_path

    def _build_wan22_workflow(self, prompt: str, conditioning: Dict, duration: float, seed: int) -> dict:
        """Load the template workflow and inject character LoRAs + prompt."""
        if self.workflow_template.exists():
            workflow = json.loads(self.workflow_template.read_text())
        else:
            workflow = {}

        if "1" in workflow:
            workflow["1"]["inputs"]["text"] = prompt + conditioning.get("prompt_suffix", "")

        if conditioning.get("lora_high") and "6" in workflow:
            workflow["6"]["inputs"]["lora_name"] = Path(conditioning["lora_high"]).name
        if conditioning.get("lora_low") and "8" in workflow:
            workflow["8"]["inputs"]["lora_name"] = Path(conditioning["lora_low"]).name

        for node_id in ("10", "11"):
            if node_id in workflow:
                workflow[node_id]["inputs"]["seed"] = seed

        frames = max(16, int(duration * 16))
        if "9" in workflow:
            workflow["9"]["inputs"]["length"] = frames

        return workflow

    async def close(self):
        await self.client.aclose()
