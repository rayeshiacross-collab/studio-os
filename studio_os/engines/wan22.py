"""
Open-source video generation engine using ComfyUI + Wan 2.2.

All generation is local and free. Character consistency is enforced
via CanonicalCharacter conditioning (LoRAs + reference images).

Workflow template: workflows/wan22_character_locked_t2v.json
"""

from pathlib import Path
from typing import Dict, List, Optional
import asyncio
import json
import uuid

class Wan22Engine:
    """
    Drives ComfyUI workflows for Wan 2.2 video generation.
    Assumes ComfyUI is running (locally or in Docker) with Wan 2.2 models loaded.
    """

    def __init__(self, comfyui_url: str = "http://localhost:8188"):
        self.comfyui_url = comfyui_url
        self.workflow_template = Path(__file__).parent.parent.parent / "workflows" / "wan22_character_locked_t2v.json"

    async def generate_clip(
        self,
        prompt: str,
        character_conditioning: Optional[Dict] = None,
        duration_seconds: float = 5.0,
        output_path: Path = None,
        seed: Optional[int] = None,
    ) -> Path:
        """
        Generate a short video clip with optional strict character lock.
        
        character_conditioning comes from CharacterConsistencyEngine.get_conditioning()
        """
        if output_path is None:
            output_path = Path(f"./renders/{uuid.uuid4()}.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        workflow = self._build_wan22_workflow(
            prompt=prompt,
            conditioning=character_conditioning or {},
            duration=duration_seconds,
            seed=seed or 42,
        )

        # TODO: POST to ComfyUI /prompt endpoint and poll for completion
        print(f"[Wan22] Generating clip → {output_path}")
        print(f"  Prompt: {prompt[:80]}...")
        if character_conditioning:
            print(f"  Character lock: {character_conditioning.get('trigger_word', 'ref-only')}")
            if character_conditioning.get("lora_high"):
                print(f"  High LoRA: {character_conditioning['lora_high']}")
            if character_conditioning.get("lora_low"):
                print(f"  Low LoRA: {character_conditioning['lora_low']}")

        await asyncio.sleep(1)
        output_path.write_text(json.dumps({"status": "stub", "workflow_nodes": list(workflow.keys())}))
        return output_path

    def _build_wan22_workflow(self, prompt: str, conditioning: Dict, duration: float, seed: int) -> dict:
        """
        Load the template workflow and inject character LoRAs + prompt.
        """
        if self.workflow_template.exists():
            workflow = json.loads(self.workflow_template.read_text())
        else:
            workflow = {}

        # Inject prompt (node 1 is positive)
        if "1" in workflow:
            workflow["1"]["inputs"]["text"] = prompt + conditioning.get("prompt_suffix", "")

        # Inject character LoRAs if present
        if conditioning.get("lora_high") and "6" in workflow:
            workflow["6"]["inputs"]["lora_name"] = Path(conditioning["lora_high"]).name
        if conditioning.get("lora_low") and "8" in workflow:
            workflow["8"]["inputs"]["lora_name"] = Path(conditioning["lora_low"]).name

        # Seed
        for node_id in ("10", "11"):
            if node_id in workflow:
                workflow[node_id]["inputs"]["seed"] = seed

        # Approximate length from duration (16 fps default)
        frames = max(16, int(duration * 16))
        if "9" in workflow:
            workflow["9"]["inputs"]["length"] = frames

        return workflow
