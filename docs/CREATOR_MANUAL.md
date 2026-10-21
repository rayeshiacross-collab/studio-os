# Studio OS Video Creator Manual

A simple guide for making videos with consistent characters using Studio OS.

---

## What You Need

- Studio OS running (local preferred)
- A character you want to use (or create one)
- A clear idea of the video (short, scene, or episode)
- Free video editor (see recommendations below)

---

## Step 1: Set Up Your Character (Do This Once)

1. Gather 4–8 good photos of the character:
   - Clear face shots (front and slight angles)
   - One full-body shot
   - Same lighting if possible

2. (Recommended) Create a character LoRA:
   - Train a high-noise and low-noise LoRA for Wan 2.2
   - Give it a unique trigger word (example: `char_alice_v1`)

3. Register the character in Studio OS so the system remembers the face forever.

**Rule**: Once registered, the face stays the same. Only clothes, hair style, and scenes change.

---

## Step 2: Choose Your Lane

| What you're making | Use this lane | Notes |
|--------------------|---------------|-------|
| High-quality short or film scene | **Artist** | Slowest, best quality, needs approval |
| Regular shorts or trailers | **Platform** | Balanced |
| Lots of quick shorts | **Farm** | Fast, less strict |
| Multi-episode series / YouTube show | **Series** | Strictest consistency, needs approval every episode |

For anything with the same character across multiple videos, prefer **Series**.

---

## Step 3: Write Your Prompt

Keep it simple and clear.

**Good example**:
> Alice walks through a rainy neon city at night, wearing a red jacket, looking determined.

**Tips**:
- Mention the character name + trigger word if you have one.
- Describe clothes and action, not the face (the system locks the face).
- Keep clips short (3–5 seconds works best with Wan 2.2).

---

## Step 4: Generate

1. Select the character.
2. Choose the lane.
3. Enter your prompt.
4. Start generation.

The system automatically applies the character lock (reference images + LoRA) so the person stays the same.

For Series:
- The system checks continuity before generating.
- You must approve the episode before the next one can use it as the baseline.

---

## Step 5: Review and Approve

- Watch the clip.
- If the face looks off, reject and regenerate.
- If clothes or scene are wrong, adjust the prompt and try again.
- Once it looks right, approve it (especially important for Series).

---

## Step 6: Edit and Finish

Studio OS generates short clips. Use a free editor to:
- Join clips into longer scenes or episodes
- Add titles, music, sound effects, and subtitles
- Color grade for consistency
- Export the final video

### Recommended Free Video Editors

| Software | Type | Best For | Notes |
|----------|------|----------|-------|
| **DaVinci Resolve** (free) | Desktop | Best overall finishing | Extremely powerful color, audio, and editing. No watermark. Free version is excellent. |
| **Shotcut** | Open source | Lightweight editing | Cross-platform, no watermark, good for older computers. |
| **Kdenlive** | Open source | Full timeline editing | Solid multi-track editor, proxy support, active development. |
| **OpenShot** | Open source | Beginners | Easy drag-and-drop, 3D titles, simple effects. |
| **LosslessCut** | Open source | Quick cuts | Trim and join without re-encoding (fast and quality-preserving). |
| **Blender** | Open source | VFX / compositing | Use if you need advanced effects or motion graphics. |
| **FFmpeg** | Open source CLI | Batch processing | Command-line tool for converting, concatenating, or basic edits. |

**Recommended starting point**:
- Beginners → OpenShot or Shotcut
- Serious finishing → DaVinci Resolve (free)
- Pure open-source preference → Kdenlive or Shotcut

All of these are free and fit the Studio OS goal of zero ongoing cost.

---

## Quick Tips for Better Results

- **Face consistency**: Always use the registered character. Don't describe the face in the prompt.
- **Clothes**: Describe clothing clearly in every prompt if you want a specific outfit.
- **Length**: Start with short clips and chain them if you need longer scenes.
- **Lighting**: Mention lighting (night, soft daylight, neon, etc.) so scenes match better.
- **Local is best**: Running on your own computer is free and private.
- **Editing**: Export clips from Studio OS, then finish them in Resolve or Kdenlive for a polished result.

---

## Common Problems

| Problem | Fix |
|---------|-----|
| Face looks different | Make sure the character is registered and the LoRA is loaded |
| Clothes wrong | Be more specific in the prompt |
| Clip too short or blurry | Lower resolution or fewer frames, then upscale later if needed |
| Series continuity failed | Re-register the character or check that you didn't change the references |
| Need longer video | Generate multiple clips and edit them together in Resolve/Shotcut/Kdenlive |

---

## Remember

- Same person, different clothes = good.
- Different face = not allowed.
- Approve before moving forward on series work.
- Free and open-source is the goal — local hardware + free editors keep costs at zero.

That's it. Create, lock the character, generate, review, edit, approve.
