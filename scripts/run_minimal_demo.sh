#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_DIR="$ROOT_DIR/.demo"
VENV_DIR="$ROOT_DIR/.venv"
FRONTEND_DIR="$ROOT_DIR/frontend_v2"
BACKEND_PID_FILE="$DEMO_DIR/backend.pid"
FRONTEND_PID_FILE="$DEMO_DIR/frontend.pid"
BACKEND_LOG="$DEMO_DIR/backend.log"
FRONTEND_LOG="$DEMO_DIR/frontend.log"

mkdir -p "$DEMO_DIR"

log() {
  printf '[demo] %s\n' "$*"
}

fail() {
  printf '[demo] ERROR: %s\n' "$*" >&2
  exit 1
}

require_file() {
  local file_path="$1"
  [[ -f "$file_path" ]] || fail "Missing file: $file_path"
}

is_pid_running() {
  local pid="$1"
  kill -0 "$pid" >/dev/null 2>&1
}

stop_pid_file() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if [[ -n "$pid" ]] && is_pid_running "$pid"; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
    rm -f "$pid_file"
  fi
}

ensure_env_files() {
  require_file "$ROOT_DIR/.env"

  if [[ ! -f "$FRONTEND_DIR/.env.local" && -f "$FRONTEND_DIR/.env.example" ]]; then
    cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env.local"
    log "Created frontend_v2/.env.local from frontend_v2/.env.example"
  fi
}

ensure_python_env() {
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    log "Creating Python virtual environment"
    python3 -m venv "$VENV_DIR"
  fi

  log "Installing Python dependencies"
  "$VENV_DIR/bin/pip" install -r "$ROOT_DIR/requirements.txt" >/dev/null
}

ensure_frontend_deps() {
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    log "Installing frontend dependencies"
    (cd "$FRONTEND_DIR" && npm install >/dev/null)
  fi
}

start_dependencies() {
  log "Starting MySQL and ChromaDB"
  (cd "$ROOT_DIR" && docker compose up -d mysql_db chromadb >/dev/null)
}

run_migrations() {
  log "Running database migrations"
  (cd "$ROOT_DIR" && "$VENV_DIR/bin/python" -m alembic -c backend/alembic.ini upgrade head >/dev/null)
}

wait_for_http() {
  local url="$1"
  local label="$2"
  local attempts=30
  local i
  for ((i=1; i<=attempts; i+=1)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "$label is ready"
      return 0
    fi
    sleep 1
  done
  fail "$label did not become ready: $url"
}

start_backend() {
  if [[ -f "$BACKEND_PID_FILE" ]] && is_pid_running "$(cat "$BACKEND_PID_FILE")"; then
    log "Backend already running"
    return 0
  fi

  log "Starting backend API"
  (
    cd "$ROOT_DIR"
    nohup "$VENV_DIR/bin/python" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 \
      >"$BACKEND_LOG" 2>&1 &
    echo $! >"$BACKEND_PID_FILE"
  )

  wait_for_http "http://127.0.0.1:8001/api/v1/health" "Backend API"
}

start_frontend() {
  if [[ -f "$FRONTEND_PID_FILE" ]] && is_pid_running "$(cat "$FRONTEND_PID_FILE")"; then
    log "Frontend already running"
    return 0
  fi

  log "Starting frontend console"
  (
    cd "$FRONTEND_DIR"
    nohup npm run dev -- --host 127.0.0.1 >"$FRONTEND_LOG" 2>&1 &
    echo $! >"$FRONTEND_PID_FILE"
  )

  wait_for_http "http://127.0.0.1:5173" "Frontend console"
}

show_status() {
  local backend_status="stopped"
  local frontend_status="stopped"

  if [[ -f "$BACKEND_PID_FILE" ]] && is_pid_running "$(cat "$BACKEND_PID_FILE")"; then
    backend_status="running"
  fi
  if [[ -f "$FRONTEND_PID_FILE" ]] && is_pid_running "$(cat "$FRONTEND_PID_FILE")"; then
    frontend_status="running"
  fi

  printf 'backend: %s\n' "$backend_status"
  printf 'frontend: %s\n' "$frontend_status"
  printf 'health: %s\n' "$(curl -fsS http://127.0.0.1:8001/api/v1/health >/dev/null 2>&1 && echo ok || echo unavailable)"
  printf 'console: %s\n' "$(curl -fsS http://127.0.0.1:5173 >/dev/null 2>&1 && echo ok || echo unavailable)"
  printf 'logs:\n'
  printf '  %s\n' "$BACKEND_LOG"
  printf '  %s\n' "$FRONTEND_LOG"
}

run_generator() {
  ensure_env_files
  ensure_python_env
  log "Running batch_generator.py in foreground"
  (
    cd "$ROOT_DIR"
    "$VENV_DIR/bin/python" batch_generator.py
  )
}

up() {
  ensure_env_files
  ensure_python_env
  ensure_frontend_deps
  start_dependencies
  run_migrations
  start_backend
  start_frontend

  cat <<EOF

Minimal demo is ready.

- API: http://127.0.0.1:8001/api/v1
- Console: http://127.0.0.1:5173
- Backend log: $BACKEND_LOG
- Frontend log: $FRONTEND_LOG

Next step:
  ./scripts/run_minimal_demo.sh run

Stop services:
  ./scripts/run_minimal_demo.sh down
EOF
}

down() {
  log "Stopping local demo processes"
  stop_pid_file "$BACKEND_PID_FILE"
  stop_pid_file "$FRONTEND_PID_FILE"

  log "Stopping MySQL and ChromaDB containers"
  (cd "$ROOT_DIR" && docker compose stop mysql_db chromadb >/dev/null || true)

  log "Minimal demo stopped"
}

usage() {
  cat <<EOF
Usage: ./scripts/run_minimal_demo.sh <command>

Commands:
  up      Start MySQL, ChromaDB, backend API, and frontend console
  run     Run batch_generator.py in the foreground
  status  Show local demo status
  down    Stop local demo processes and supporting containers
EOF
}

COMMAND="${1:-up}"

case "$COMMAND" in
  up)
    up
    ;;
  run)
    run_generator
    ;;
  status)
    show_status
    ;;
  down)
    down
    ;;
  *)
    usage
    exit 1
    ;;
esac
