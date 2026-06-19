#!/usr/bin/env bash
# Steuerung der gesamten Anwendung: ./start.sh [start|stop|restart|status]
set -uo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN="$HIER/.run"
mkdir -p "$RUN"
ENVFILE="$HIER/.env"

# Konfiguration mit derselben Rangfolge wie das Backend lesen:
# bereits gesetzte Umgebungsvariable > .env > Standardwert.
envget() {
  local key="$1" def="$2" val="${!key:-}"
  if [ -z "$val" ] && [ -f "$ENVFILE" ]; then
    val="$(sed -n "s/^${key}=//p" "$ENVFILE" | head -1)"
    val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
  fi
  printf '%s' "${val:-$def}"
}

# Standard ist die reine localhost-Bindung. Die API ist unauthentifiziert; eine
# Bindung an eine nicht-lokale Adresse gibt sie ungeschuetzt im Netz frei.
BIND="$(envget PINNWAND_BIND 127.0.0.1)"
BPORT="$(envget PINNWAND_BACKEND_PORT 8420)"
FPORT="$(envget PINNWAND_FRONTEND_PORT 5198)"

listener() { lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null; }

backend_start() {
  cd "$HIER/backend"
  if [ ! -d .venv ]; then
    python3 -m venv .venv
    ./.venv/bin/pip install -q -r requirements.txt
  fi
  nohup ./.venv/bin/uvicorn app.main:app --host "$BIND" --port "$BPORT" --log-level warning > "$RUN/backend.log" 2>&1 &
  echo $! > "$RUN/backend.pid"
}

frontend_start() {
  cd "$HIER/frontend"
  [ -d node_modules ] || npm install
  nohup npm run dev -- --port "$FPORT" --strictPort > "$RUN/frontend.log" 2>&1 &
  echo $! > "$RUN/frontend.pid"
}

stop_all() {
  for f in backend frontend; do
    if [ -f "$RUN/$f.pid" ]; then
      kill "$(cat "$RUN/$f.pid")" 2>/dev/null
      rm -f "$RUN/$f.pid"
    fi
  done
  for p in "$BPORT" "$FPORT"; do
    pids="$(listener "$p")"
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null
  done
}

status() {
  for pair in "Backend $BPORT" "Frontend $FPORT"; do
    set -- $pair
    if [ -n "$(listener "$2")" ]; then echo "$1 ($2): laeuft"; else echo "$1 ($2): aus"; fi
  done
}

case "${1:-start}" in
  start)
    stop_all; sleep 1
    backend_start; frontend_start
    echo "Pinnwand gestartet -> Frontend http://localhost:$FPORT  ·  API http://localhost:$BPORT"
    echo "Logs: $RUN/backend.log , $RUN/frontend.log"
    ;;
  stop)
    stop_all
    echo "Pinnwand gestoppt"
    ;;
  restart)
    stop_all; sleep 1
    backend_start; frontend_start
    echo "Pinnwand neu gestartet -> http://localhost:$FPORT"
    ;;
  status)
    status
    ;;
  *)
    echo "Nutzung: $0 [start|stop|restart|status]"
    exit 1
    ;;
esac
