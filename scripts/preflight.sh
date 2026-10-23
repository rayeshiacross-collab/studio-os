#!/usr/bin/env bash
set -euo pipefail
COMFYUI_URL="${COMFYUI_URL:-http://localhost:8188}"
echo "Studio OS preflight"
python -m compileall -q studio_os
python -m pip check
if command -v ffmpeg >/dev/null 2>&1; then ffmpeg -version | head -n 1; else echo "WARN: ffmpeg missing"; fi
if command -v docker >/dev/null 2>&1; then docker compose config --quiet; else echo "WARN: docker missing"; fi
if curl --fail --silent --show-error --max-time 8 "${COMFYUI_URL%/}/system_stats" >/dev/null; then
  echo "PASS: ComfyUI responds"
else
  echo "FAIL: ComfyUI unavailable at configured host" >&2
  exit 1
fi
echo "Preflight passed; model availability and actual video render still require testing."
