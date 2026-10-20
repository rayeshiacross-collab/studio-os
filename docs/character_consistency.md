# Character Consistency Workflow

**The person cannot change. Clothes can.**

## Setup a Canonical Character

1. Collect 4–8 clean reference images:
   - Face close-ups (front, 3/4, slight smile)
   - Full body (neutral pose)
   - Same lighting preferred

2. (Recommended) Train a Wan 2.2 character LoRA:
   - Use AI Toolkit or Kohya
   - Train both high-noise and low-noise LoRAs
   - Use a unique trigger word (e.g. `char_alice_v1`)

3. Register in Studio OS:

```python
from studio_os.core.character_consistency import CanonicalCharacter, CharacterConsistencyEngine

engine = CharacterConsistencyEngine()
char = CanonicalCharacter(
    id="alice",
    name="Alice",
    reference_images=[Path("refs/alice_face1.png"), Path("refs/alice_body.png")],
    lora_high_noise=Path("loras/alice_high.safetensors"),
    lora_low_noise=Path("loras/alice_low.safetensors"),
    trigger_word="char_alice_v1",
    notes="Same face always. Clothes and hair style can vary by scene."
)
engine.register(char)
```

## In Production

Every generation call in any lane (especially **Series**) must pass the conditioning:

```python
conditioning = engine.get_conditioning("alice")
clip = await wan_engine.generate_clip(
    prompt="Alice walks through a neon city at night, wearing a red jacket",
    character_conditioning=conditioning,
)
```

The Series lane forces this and requires approval before moving to the next episode.
