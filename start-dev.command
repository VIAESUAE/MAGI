#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT_DIR"
echo "[MAGI] Starting backend on :8000 ..."
python3 -m uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

cleanup() {
  echo
  echo "[MAGI] Stopping backend (pid=$BACKEND_PID) ..."
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "[MAGI] Starting frontend on :5173 ..."
cd "$ROOT_DIR/frontend"
npm run dev
