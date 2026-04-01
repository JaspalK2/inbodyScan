#!/usr/bin/env bash
# Start all microservices locally for development.
# Run from the repo root: ./scripts/start-local.sh
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env not found. Copy .env.example and fill in values."
  exit 1
fi

set -a; source "$ENV_FILE"; set +a

start_service() {
  local name=$1
  local port=$2
  local dir="$ROOT/services/$name"
  echo "Starting $name on port $port..."
  cd "$dir"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements.txt
  fi
  .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port "$port" --reload &
  cd "$ROOT"
}

start_service auth-service 8001
start_service user-service 8002
start_service scan-service 8003
start_service analytics-service 8004
start_service recommendation-service 8005
start_service admin-service 8006

echo ""
echo "All services started. Press Ctrl+C to stop."
wait
