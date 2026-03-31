#!/usr/bin/env bash
set -euo pipefail

# Simple verification wrapper. Attempts to run ruff (ALL), then ty, and falls back to pyrefly.
# It does NOT install tools automatically; install them in your preferred env manager (venv, poetry, uv, etc.).

echo "Running ruff (select ALL) if available..."
if command -v ruff >/dev/null 2>&1; then
  ruff check . --select ALL
else
  echo "ruff not found. Install with: pip install ruff"
fi

echo "\nRunning ty type checker if available..."
if command -v ty >/dev/null 2>&1; then
  ty check . || true
else
  echo "ty not found. If you expect 'ty' to be available, install it, or use 'pyrefly' as a fallback."
  if command -v pyrefly >/dev/null 2>&1; then
    echo "pyrefly found — running pyrefly check as fallback"
    pyrefly check . || true
  else
    echo "pyrefly not found either. Install with: pip install pyrefly"
  fi
fi

cat <<EOF

Notes:
- To run these inside an isolated env using Python venv:
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\Activate on Windows
    pip install ruff ty pyrefly
    ./scripts/verify.sh
- For Astral / uv usage: upload workspace or run the same commands in your Astral/uv environment and select ruff with ALL rules.
EOF
