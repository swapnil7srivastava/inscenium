#!/usr/bin/env zsh
set -euo pipefail
IFS=$'\n\t'

# ------------------------------------------------------------------------------
# fix_inscenium_env.sh — Idempotent macOS zsh script to set up slim runtime venv
# and perform optional Poetry hygiene for the Inscenium project.
# ------------------------------------------------------------------------------

# Create timestamped log file and tee all output
LOG_FILE="inscenium_env_fix_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Error trap to surface log path on failure
trap 'echo "❌ Failed. See log: $LOG_FILE" >&2; exit 1' ERR

echo "→ Starting Inscenium environment fix at $(date)"
echo "→ Log file: $LOG_FILE"

# Normalize PATH early (strip CRs and any embedded 'Unknown command:' fragments)
PATH="$(print -r -- "$PATH" | tr -d '\r' | sed -E 's#[^:]*Unknown command:[^:]*:##g')"
export PATH
echo "→ Normalized PATH"

# Environment toggles with defaults
PY_VERSION=${PY_VERSION:-3.11}
POETRY_HYGIENE=${POETRY_HYGIENE:-1}    # 1=on, 0=off
FORCE_RECREATE=${FORCE_RECREATE:-1}    # 1=delete existing .venv-runtime
PIP_INDEX_URL_CPU=${PIP_INDEX_URL_CPU:-https://download.pytorch.org/whl/cpu}

echo "→ Environment: PY_VERSION=$PY_VERSION  POETRY_HYGIENE=$POETRY_HYGIENE  FORCE_RECREATE=$FORCE_RECREATE"

# Verify project root
if [[ ! -f "pyproject.toml" ]]; then
  echo "❌ Error: pyproject.toml not found. Run this from the project root."
  exit 1
fi
echo "✓ Found pyproject.toml"

# Python selection
PYTHON_CMD=""
if command -v pyenv >/dev/null 2>&1; then
  echo "→ pyenv detected; looking for python${PY_VERSION}"
  if ! pyenv which "python${PY_VERSION}" >/dev/null 2>&1; then
    echo "→ python${PY_VERSION} missing in pyenv; installing ${PY_VERSION}.9 (patch)"
    pyenv install -s "${PY_VERSION}.9"
  fi
  PYENV_PYTHON="$(pyenv which "python${PY_VERSION}" 2>/dev/null || true)"
  if [[ -n "${PYENV_PYTHON}" && -x "${PYENV_PYTHON}" ]]; then
    PYTHON_CMD="${PYENV_PYTHON}"
    echo "✓ Using pyenv Python: ${PYTHON_CMD}"
  fi
fi

if [[ -z "${PYTHON_CMD}" ]]; then
  if command -v "python${PY_VERSION}" >/dev/null 2>&1; then
    PYTHON_CMD="python${PY_VERSION}"
    echo "✓ Using system Python: ${PYTHON_CMD}"
  else
    echo "❌ Error: Neither pyenv python${PY_VERSION} nor system python${PY_VERSION} found."
    exit 1
  fi
fi

echo "→ Selected Python interpreter: ${PYTHON_CMD}"

# Part A — Slim runtime venv (independent of Poetry)
echo "→ Part A: Preparing slim runtime venv at .venv-runtime"

if [[ "${FORCE_RECREATE}" == "1" && -d ".venv-runtime" ]]; then
  echo "→ FORCE_RECREATE=1: removing existing .venv-runtime"
  rm -rf .venv-runtime
fi

if [[ ! -d ".venv-runtime" ]]; then
  echo "→ Creating .venv-runtime with ${PYTHON_CMD}"
  "${PYTHON_CMD}" -m venv .venv-runtime
else
  echo "→ Reusing existing .venv-runtime"
fi

echo "→ Activating .venv-runtime"
source .venv-runtime/bin/activate

echo "→ Upgrading base tooling (pip/wheel/setuptools)"
python -m pip install -U "pip<25.4" wheel setuptools

echo "→ Installing PyTorch CPU wheels from ${PIP_INDEX_URL_CPU}"
python -m pip install --index-url "${PIP_INDEX_URL_CPU}" "torch==2.2.2" "torchvision==0.17.2"

echo "→ Installing core runtime deps"
python -m pip install "pillow>=10.2.0" "pydantic>=2.7" "numpy==1.26.4"

echo "→ Sanity check (versions)"
python - <<'PYCHECK'
import sys, torch, torchvision, PIL, pydantic, numpy
print(f"✓ Python: {sys.version.split()[0]}")
print(f"✓ torch: {torch.__version__}")
print(f"✓ torchvision: {torchvision.__version__}")
print(f"✓ Pillow: {PIL.__version__}")
print(f"✓ pydantic: {pydantic.__version__}")
print(f"✓ numpy: {numpy.__version__}")
PYCHECK

echo "→ Deactivating venv"
deactivate

echo "→ Clearing macOS quarantine and fixing interpreter permissions"
xattr -dr com.apple.quarantine .venv-runtime || true
chmod +x .venv-runtime/bin/python

INTERPRETER_PATH="$PWD/.venv-runtime/bin/python"
echo "✓ Runtime venv ready at: $INTERPRETER_PATH"
echo "→ Use this in PyCharm: $INTERPRETER_PATH"

# Part B — Poetry hygiene (ON by default)
if [[ "${POETRY_HYGIENE}" == "1" && "$(command -v poetry || true)" != "" ]]; then
  echo "→ Part B: Running Poetry hygiene"

  # In-place TOML text patcher (no third-party deps)
  python3 <<'PYTOML'
import re, sys

path = 'pyproject.toml'
try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        had_trailing_nl = content.endswith('\n')
except FileNotFoundError:
    print("❌ Error: pyproject.toml not found", flush=True)
    sys.exit(1)

required = {
    'name': '"inscenium"',
    'version': '"1.0.0"',
    'package-mode': 'false',
}

m = re.search(r'(?m)^\[tool\.poetry\]\s*$', content)
if m:
    start = m.start()
    m2 = re.search(r'(?m)^\[[^\]]+\]\s*$', content[m.end():])
    end = m.end() + (m2.start() if m2 else len(content) - m.end())
    section = content[start:end]
    for k, v in required.items():
        pat = re.compile(rf'(?m)^{re.escape(k)}\s*=\s*.*$')
        line = f'{k} = {v}'
        if pat.search(section):
            section = pat.sub(line, section)
        else:
            lines = section.splitlines()
            if lines:
                lines.insert(1, line)
                section = "\n".join(lines) + ("\n" if section.endswith("\n") else "")
            else:
                section = f"[tool.poetry]\n{line}\n"
    new = content[:start] + section + content[end:]
else:
    if not content.endswith('\n'):
        content += '\n'
    block = "[tool.poetry]\n" + "\n".join(f"{k} = {v}" for k, v in required.items()) + "\n"
    new = content + "\n" + block

if had_trailing_nl and not new.endswith('\n'):
    new += '\n'
elif not had_trailing_nl and new.endswith('\n'):
    new = new.rstrip('\n')

with open(path, 'w', encoding='utf-8') as f:
    f.write(new)

print("✓ Updated pyproject.toml [tool.poetry] keys", flush=True)
PYTOML

  echo "→ Ensuring numpy<2.0 in poetry"
  poetry add -n "numpy<2.0" || true

  echo "→ Regenerating poetry.lock (no cache)"
  poetry lock --no-cache --regenerate

  echo "→ Installing main dependencies (no root)"
  poetry install -n --only main --no-root

  echo "✓ Poetry hygiene completed"
else
  if [[ "${POETRY_HYGIENE}" != "1" ]]; then
    echo "→ Poetry hygiene skipped (POETRY_HYGIENE=${POETRY_HYGIENE})"
  else
    echo "→ Poetry hygiene skipped (poetry not found on PATH)"
  fi
fi

echo ""
echo "🎉 Inscenium environment fix completed successfully!"
echo "🐍 PyCharm interpreter: $INTERPRETER_PATH"
echo "📁 Log file: $LOG_FILE"
echo "📋 Next step: Select this interpreter in PyCharm."
