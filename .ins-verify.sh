#!/usr/bin/env bash
set -e -o pipefail

red(){ printf "\033[31m%s\033[0m\n" "$*"; }
grn(){ printf "\033[32m%s\033[0m\n" "$*"; }
ylw(){ printf "\033[33m%s\033[0m\n" "$*"; }

chk(){ local name cmd_status
  name="$1"; shift
  if "$@"; then grn "✓ $name"; cmd_status=0; else red "✗ $name"; cmd_status=1; fi
  return "$cmd_status"
}

# 0) Repo basics
chk "pyproject.toml present" test -f pyproject.toml
chk "Makefile present"       test -f Makefile
chk "fix script present"     test -x fix_inscenium_env.sh
chk "cpu profile present"    test -f configs/pipeline/cpu_default.yaml

# 1) Poetry available (install via pipx if missing)
if ! command -v poetry >/dev/null 2>&1; then
  ylw "• Poetry not found; installing via pipx"
  python3 -m pip install --user -q pipx || true
  python3 -m pipx ensurepath || true
  pipx install poetry || true
  command -v poetry >/dev/null 2>&1 || { red "✗ Poetry unavailable"; exit 1; }
fi

# 2) Env bootstrap + smoke
INS_LOG_FORMAT=plain ./fix_inscenium_env.sh
make smoke

# 3) Lock & install (dev included), no project install
poetry lock
poetry install --no-interaction --with dev --no-root

# 4) CLI entry & flags
poetry run inscenium --help > /tmp/ins_help.txt
grep -qE "\bvideo\b" /tmp/ins_help.txt || { red "✗ CLI missing video command"; exit 1; }
poetry run inscenium video --help > /tmp/ins_video_help.txt
grep -q -- "--render-overlay" /tmp/ins_video_help.txt || { red "✗ CLI missing --render-overlay flag"; exit 1; }

# 5) Sample video (generate if missing)
if [ ! -f samples/demo.mp4 ]; then
  mkdir -p samples
  python3 - <<PY
import cv2, numpy as np
w,h=640,360; fourcc=cv2.VideoWriter_fourcc(*"mp4v")
v=cv2.VideoWriter("samples/demo.mp4", fourcc, 24, (w,h))
for i in range(96):
    f=np.zeros((h,w,3),np.uint8)
    cv2.rectangle(f,(50+i,120),(150+i,220),(0,255,0),-1)
    v.write(f)
v.release()
print("generated samples/demo.mp4")
PY
fi

# 6) Short CPU run
RUN_DIR="runs/verify_$(date +%Y%m%d_%H%M%S)"
INS_LOG_FORMAT=plain INS_FORCE_CPU=1 poetry run inscenium video \
  --in samples/demo.mp4 \
  --out "$RUN_DIR" \
  --profile cpu \
  --render-overlay yes \
  --every-nth 2 \
  --max-frames 60 || { red "✗ Pipeline run failed"; exit 1; }

# 7) Artifacts
need=0
for f in "$RUN_DIR/overlay.mp4" "$RUN_DIR/events.sgi.jsonl" "$RUN_DIR/metrics.json" "$RUN_DIR/run.json"; do
  if [ -f "$f" ]; then grn "✓ Artifact: ${f#./}"; else red "✗ Missing: ${f#./}"; need=1; fi
done

# 8) Smoke versions file (non-fatal if absent)
if [ -f runs/_latest/smoke_versions.txt ]; then
  grn "✓ Smoke versions: runs/_latest/smoke_versions.txt"
else
  ylw "• Smoke versions missing (non-fatal)"
fi

# 9) Quick content sanity (jq optional)
if ! head -n 1 "$RUN_DIR/events.sgi.jsonl" >/dev/null; then red "✗ SGI file empty"; need=1; fi
if command -v jq >/dev/null 2>&1; then
  jq -e . "$RUN_DIR/metrics.json" >/dev/null 2>&1 || ylw "• metrics.json not pretty JSON (ok if minimal writer)"
fi

# 10) Summary
if [ "$need" -ne 0 ]; then
  red "❌ Verification failed. See: $RUN_DIR"
  exit 2
fi
grn "✅ All checks passed."
echo "Interpreter: $(pwd)/.venv-runtime/bin/python"
echo "Next: poetry run inscenium video --in samples/demo.mp4 --out runs/demo --profile cpu --render-overlay yes"
