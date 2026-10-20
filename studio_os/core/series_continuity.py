"""
Series lane episode-level continuity checks.

Ensures character identity stays locked across episodes of a series.
Clothes and scenes can change; the person cannot.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

@dataclass
class EpisodeContinuityRecord:
    """Tracks what was established in previous episodes."""
    series_id: str
    episode_number: int
    character_ids: List[str]
    canonical_refs_used: Dict[str, str]  # character_id -> identity_hash
    key_scenes: List[str] = field(default_factory=list)
    clothing_notes: Dict[str, str] = field(default_factory=dict)  # character_id -> outfit description
    created_at: datetime = field(default_factory=datetime.now)
    approved: bool = False

    def to_dict(self) -> dict:
        return {
            "series_id": self.series_id,
            "episode_number": self.episode_number,
            "character_ids": self.character_ids,
            "canonical_refs_used": self.canonical_refs_used,
            "key_scenes": self.key_scenes,
            "clothing_notes": self.clothing_notes,
            "created_at": self.created_at.isoformat(),
            "approved": self.approved,
        }


class SeriesContinuityManager:
    """
    Episode-level continuity for the Series lane.
    Every new episode must re-anchor to the same CanonicalCharacter profiles.
    """

    def __init__(self, continuity_dir: Path = Path("./series_continuity")):
        self.continuity_dir = continuity_dir
        self.continuity_dir.mkdir(parents=True, exist_ok=True)

    def _series_path(self, series_id: str) -> Path:
        return self.continuity_dir / f"{series_id}.json"

    def load_series(self, series_id: str) -> List[EpisodeContinuityRecord]:
        path = self._series_path(series_id)
        if not path.exists():
            return []
        data = json.loads(path.read_text())
        records = []
        for item in data:
            rec = EpisodeContinuityRecord(
                series_id=item["series_id"],
                episode_number=item["episode_number"],
                character_ids=item["character_ids"],
                canonical_refs_used=item["canonical_refs_used"],
                key_scenes=item.get("key_scenes", []),
                clothing_notes=item.get("clothing_notes", {}),
                approved=item.get("approved", False),
            )
            records.append(rec)
        return records

    def save_episode(self, record: EpisodeContinuityRecord):
        records = self.load_series(record.series_id)
        # Replace if same episode number already exists
        records = [r for r in records if r.episode_number != record.episode_number]
        records.append(record)
        records.sort(key=lambda r: r.episode_number)
        path = self._series_path(record.series_id)
        path.write_text(json.dumps([r.to_dict() for r in records], indent=2))

    def check_episode_continuity(
        self,
        series_id: str,
        episode_number: int,
        character_ids: List[str],
        character_engine,
    ) -> Dict:
        """
        Validate that this episode uses the same locked characters as previous episodes.
        Returns a report with pass/fail and any drift warnings.
        """
        previous = self.load_series(series_id)
        report = {
            "series_id": series_id,
            "episode_number": episode_number,
            "passed": True,
            "warnings": [],
            "errors": [],
            "required_characters": [],
        }

        if not previous:
            # First episode — just record the baseline
            report["warnings"].append("First episode: establishing character baseline.")
            for cid in character_ids:
                char = character_engine.get(cid)
                if char:
                    report["required_characters"].append({
                        "id": cid,
                        "identity_hash": char.identity_hash,
                        "trigger_word": char.trigger_word,
                    })
            return report

        # Subsequent episodes must match previously used character hashes
        last = previous[-1]
        established = last.canonical_refs_used

        for cid in character_ids:
            char = character_engine.get(cid)
            if not char:
                report["passed"] = False
                report["errors"].append(f"Character {cid} not registered in CharacterConsistencyEngine.")
                continue

            if cid in established:
                if char.identity_hash != established[cid]:
                    report["passed"] = False
                    report["errors"].append(
                        f"Character {cid} identity hash drifted. "
                        f"Expected {established[cid]}, got {char.identity_hash}. "
                        "Re-register with original references."
                    )
            else:
                report["warnings"].append(f"New character {cid} introduced in episode {episode_number}.")

            report["required_characters"].append({
                "id": cid,
                "identity_hash": char.identity_hash,
                "trigger_word": char.trigger_word,
            })

        # Ensure all previously established characters are still present (or explicitly retired)
        for old_cid in established:
            if old_cid not in character_ids:
                report["warnings"].append(
                    f"Character {old_cid} from previous episodes is not in this episode. "
                    "Confirm this is intentional."
                )

        return report

    def record_approved_episode(
        self,
        series_id: str,
        episode_number: int,
        character_ids: List[str],
        character_engine,
        clothing_notes: Optional[Dict[str, str]] = None,
        key_scenes: Optional[List[str]] = None,
    ):
        """Call after human approval to lock the continuity baseline for future episodes."""
        hashes = {}
        for cid in character_ids:
            char = character_engine.get(cid)
            if char:
                hashes[cid] = char.identity_hash

        record = EpisodeContinuityRecord(
            series_id=series_id,
            episode_number=episode_number,
            character_ids=character_ids,
            canonical_refs_used=hashes,
            clothing_notes=clothing_notes or {},
            key_scenes=key_scenes or [],
            approved=True,
        )
        self.save_episode(record)
        return record
