"""
Character Consistency System for Studio OS.

Ensures the same person looks the same across shots, episodes, and series.
Clothes and lighting can change; identity cannot.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict
import hashlib
import json

@dataclass
class CanonicalCharacter:
    """Locked identity for a character across all productions."""
    id: str
    name: str
    reference_images: List[Path] = field(default_factory=list)  # face + body
    lora_high_noise: Optional[Path] = None  # Wan 2.2 high-noise LoRA
    lora_low_noise: Optional[Path] = None   # Wan 2.2 low-noise LoRA
    trigger_word: str = ""
    identity_hash: str = ""
    notes: str = ""  # "same face, can change clothes"

    def __post_init__(self):
        if not self.identity_hash and self.reference_images:
            self.identity_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        h = hashlib.sha256()
        for p in sorted(self.reference_images):
            if p.exists():
                h.update(p.read_bytes())
        return h.hexdigest()[:16]

    def save(self, path: Path):
        data = {
            "id": self.id,
            "name": self.name,
            "reference_images": [str(p) for p in self.reference_images],
            "lora_high_noise": str(self.lora_high_noise) if self.lora_high_noise else None,
            "lora_low_noise": str(self.lora_low_noise) if self.lora_low_noise else None,
            "trigger_word": self.trigger_word,
            "identity_hash": self.identity_hash,
            "notes": self.notes,
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "CanonicalCharacter":
        data = json.loads(path.read_text())
        return cls(
            id=data["id"],
            name=data["name"],
            reference_images=[Path(p) for p in data["reference_images"]],
            lora_high_noise=Path(data["lora_high_noise"]) if data["lora_high_noise"] else None,
            lora_low_noise=Path(data["lora_low_noise"]) if data["lora_low_noise"] else None,
            trigger_word=data.get("trigger_word", ""),
            identity_hash=data.get("identity_hash", ""),
            notes=data.get("notes", ""),
        )


class CharacterConsistencyEngine:
    """
    Enforces character identity across all generations.
    Used by every lane, especially Series.
    """

    def __init__(self, characters_dir: Path = Path("./characters")):
        self.characters_dir = characters_dir
        self.characters_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, CanonicalCharacter] = {}

    def register(self, character: CanonicalCharacter) -> str:
        """Register or update a canonical character. Returns ID."""
        char_dir = self.characters_dir / character.id
        char_dir.mkdir(exist_ok=True)
        character.save(char_dir / "profile.json")
        self._cache[character.id] = character
        return character.id

    def get(self, character_id: str) -> Optional[CanonicalCharacter]:
        if character_id in self._cache:
            return self._cache[character_id]
        profile = self.characters_dir / character_id / "profile.json"
        if profile.exists():
            char = CanonicalCharacter.load(profile)
            self._cache[character_id] = char
            return char
        return None

    def get_conditioning(self, character_id: str) -> Dict:
        """
        Returns everything needed to condition a ComfyUI / Wan 2.2 generation
        so the character stays consistent.
        """
        char = self.get(character_id)
        if not char:
            raise ValueError(f"Character {character_id} not registered")

        return {
            "reference_images": [str(p) for p in char.reference_images],
            "lora_high": str(char.lora_high_noise) if char.lora_high_noise else None,
            "lora_low": str(char.lora_low_noise) if char.lora_low_noise else None,
            "trigger_word": char.trigger_word,
            "identity_hash": char.identity_hash,
            # For ComfyUI workflows: pass these into CLIPVision / LoRA loaders / IP-Adapter style nodes
            "prompt_suffix": f", {char.trigger_word}" if char.trigger_word else "",
        }

    def verify_output(self, character_id: str, generated_image: Path) -> bool:
        """
        Optional post-check. In production this can call a face similarity model.
        For now, returns True if character exists (extend with InsightFace or similar if desired).
        """
        return self.get(character_id) is not None
