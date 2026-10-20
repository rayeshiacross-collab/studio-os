# Series Lane — Episode Continuity

The **Series** lane is for multi-episode content (TV series, YouTube series, short films that share characters).

## Rules

1. Every character used in a series must be registered in the `CharacterConsistencyEngine` **before** episode 1.
2. The same `identity_hash` must be used across all episodes. Changing the reference images or LoRA creates a new hash and fails the check.
3. Clothes, hair styling, and lighting can change per scene. The face and core identity cannot.
4. Each episode must pass `SeriesContinuityManager.check_episode_continuity()` before generation starts.
5. After human approval, call `record_approved_episode()` to lock the baseline for the next episode.

## Usage

```python
from studio_os.core.series_continuity import SeriesContinuityManager
from studio_os.core.character_consistency import CharacterConsistencyEngine

engine = CharacterConsistencyEngine()
series = SeriesContinuityManager()

# Before generating episode 3
report = series.check_episode_continuity(
    series_id="my_youtube_series",
    episode_number=3,
    character_ids=["alice", "bob"],
    character_engine=engine,
)

if not report["passed"]:
    raise RuntimeError(f"Continuity failed: {report['errors']}")

# After approval
series.record_approved_episode(
    series_id="my_youtube_series",
    episode_number=3,
    character_ids=["alice", "bob"],
    character_engine=engine,
    clothing_notes={"alice": "red jacket, jeans", "bob": "black hoodie"},
)
```

## Integration with Orchestrator

When `LoopType.SERIES` is selected, the orchestrator should:
1. Call `check_episode_continuity` at the start of the order.
2. Inject the character conditioning into every `Wan22Engine.generate_clip` call.
3. Require approval before marking the episode complete and recording it.
