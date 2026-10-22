# Motion-only production batches

`python -m studio_os.motion_batch` connects reviewed scene plans to an existing local ComfyUI installation. It does not use a paid API, generate substitute narration, publish content, or fall back to still images.

The owner-approved content intake is stored in the owner's private production repository. This public repository contains only reusable software and synthetic test fixtures. Source documents and videos remain untouched in Drive.

## Inputs

A version 1 job contains an ID, complete narration and its SHA-256, generation dimensions, optional export dimensions, `motion_required: true`, and ordered scenes. Every scene supplies a unique ID, the exact narration segment, a concrete visible action, a full visual prompt, and `character_present: false`.

This runner accepts object/environment shots. It rejects cast shots rather than claiming that a text prompt locks an actor's identity. Registered character workflows require their own reference-conditioning implementation and review. The existing character example workflow is not certified as a working installation by this addition.

Provide an existing, reviewed narration recording. Scene spans are estimated proportionally from spoken word counts, not forced aligned; review cut timing. Long spans generate multiple clips with different seeds, rather than freezing or repeating a clip. No audio is truncated or slowed to reach a requested runtime.

Use a **tested ComfyUI API-format workflow export** from the actual Wan installation. Supply a JSON binding map for `prompt`, `width`, `height`, `length`, `seed` and `fps`. Each value is a list of `[node_id, input_name]` pairs. For the repository's illustrative graph, these are 1.text, 9.width, 9.height, 9.length, 10.seed/11.seed, 13.fps. Those node numbers are examples, not an assertion that the illustrative graph, placeholder LoRAs or video-saving node work on your server.

```sh
python -m studio_os.motion_batch path/to/job.json --validate-only
python -m studio_os.motion_batch path/to/job.json \
  --workflow tested-wan-api.json --bindings tested-bindings.json --preflight
python -m studio_os.motion_batch path/to/job.json \
  --workflow tested-wan-api.json --bindings tested-bindings.json \
  --audio reviewed-narration.wav --output renders/review
```

Preflight checks connectivity, explicit bindings and installed node classes. ComfyUI validates the complete graph and installed model choices on submission. Render polling has a deadline and surfaces server failures. Exact workflow hashes identify reusable clips; changed prompts or inputs create different cache paths. Use one process per output directory.

Each generated clip passes a complete FFmpeg decode and a temporal pixel-change test. The test rejects static/near-static output, but cannot prove meaningful acting: camera movement, noise and flicker can also pass. **Review object action, continuity, hands, style, narration match and timing before acceptance.** Receipts retain `semantic_review: pending` and `published: false`.

Output includes clips, their checksums, and a combined H.264/AAC MP4 with narration. All shots contain motion; no slide, poster or black-text fallback is implemented. Model weights, a compatible video-saving node, FFmpeg, compute and the ComfyUI service must actually exist. A validated job or a passing synthetic test is not a completed Wan render.
