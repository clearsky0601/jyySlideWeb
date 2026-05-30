#!/bin/zsh
# ============================================================
#  EasySlides — local service manager
#  Usage: ./start_local.sh [on|off|restart|status]
#    no args:  start if stopped; show menu if already running
#    on:       start service; show menu if already running
#    off:      stop service
#    restart:  restart service
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BIND_HOST="${BIND_HOST:-127.0.0.1}"
PORT="${PORT:-10001}"
URL="http://localhost:${PORT}"
RUN_DIR="$PROJECT_ROOT/.run"
PID_FILE="$RUN_DIR/easyslides.pid"
LOG_FILE="$RUN_DIR/easyslides.log"

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
CYAN=$'\033[0;36m'
DIM=$'\033[2m'
BOLD=$'\033[1m'
NC=$'\033[0m'

print_help() {
  echo ""
  echo "  ${BOLD}Usage${NC}: ./start_local.sh ${DIM}[on|off|restart|status]${NC}"
  echo ""
  echo "    ${DIM}无参数${NC}    未运行→启动 | 已运行→交互菜单"
  echo "    ${CYAN}on${NC}        启动服务，已运行则提示操作"
  echo "    ${CYAN}off${NC}       停止服务"
  echo "    ${CYAN}restart${NC}   重启服务"
  echo "    ${CYAN}status${NC}    查看状态"
  echo ""
}

is_pid_running() {
  local pid="${1:-}"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

pid_from_file() {
  if [ -f "$PID_FILE" ]; then
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if is_pid_running "$pid"; then
      echo "$pid"
      return 0
    fi
    rm -f "$PID_FILE"
  fi
  return 1
}

pid_from_port() {
  lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -1 || true
}

get_pid() {
  local pid
  pid="$(pid_from_file 2>/dev/null || true)"
  if [ -n "$pid" ]; then
    echo "$pid"
    return 0
  fi
  pid_from_port
}

is_running() {
  [ -n "$(get_pid)" ]
}

print_status() {
  local pid
  pid="$(get_pid)"
  echo ""
  if [ -n "$pid" ]; then
    echo "  ${GREEN}●${NC} ${BOLD}EasySlides is running${NC} ${DIM}(PID ${pid}, port ${PORT})${NC}"
    echo "    ${CYAN}${URL}${NC}"
    echo "    ${DIM}log: ${LOG_FILE}${NC}"
  else
    echo "  ${RED}●${NC} ${BOLD}EasySlides is stopped${NC}"
  fi
  echo ""
}

ensure_runtime() {
  cd "$PROJECT_ROOT"

  mkdir -p "$PROJECT_ROOT/media" "$RUN_DIR"
  if [ ! -f "$PROJECT_ROOT/db.sqlite3" ]; then
    touch "$PROJECT_ROOT/db.sqlite3"
  fi

  if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating virtualenv..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip >/dev/null
  python -m pip install -r "$PROJECT_ROOT/requirements.txt" >/dev/null
  python "$PROJECT_ROOT/manage.py" migrate --noinput >/dev/null

  python "$PROJECT_ROOT/manage.py" shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', '', 'admin')
    print('Created default superuser: admin/admin')
else:
    print('Superuser already exists, skipping creation')
"
}

wait_until_ready() {
  local ready=false
  local i
  for i in $(seq 1 20); do
    if curl -fsS --connect-timeout 1 "$URL/" >/dev/null 2>&1; then
      ready=true
      break
    fi
    sleep 0.5
  done

  if [ "$ready" = true ]; then
    echo "  ${GREEN}ready${NC} ${DIM}(${i} checks)${NC}"
  else
    echo "  ${YELLOW}started, health check pending${NC}"
    echo "  ${DIM}tail -f ${LOG_FILE}${NC}"
  fi
}

start_server() {
  if is_running; then
    print_running_menu
    return 0
  fi

  echo ""
  echo "  ${BOLD}EasySlides${NC} -- starting"
  ensure_runtime

  echo -n "  Starting daphne... "
  : > "$LOG_FILE"
  cd "$PROJECT_ROOT"
  local pid
  pid="$("$VENV_DIR/bin/python" - "$VENV_DIR/bin/python" "$PROJECT_ROOT" "$BIND_HOST" "$PORT" "$LOG_FILE" <<'PY'
import subprocess
import sys

python_bin, project_root, bind_host, port, log_file = sys.argv[1:]
log = open(log_file, "ab", buffering=0)
proc = subprocess.Popen(
    [
        python_bin,
        "-m",
        "daphne",
        "-b",
        bind_host,
        "-p",
        port,
        "easy_slides.asgi:application",
    ],
    cwd=project_root,
    stdin=subprocess.DEVNULL,
    stdout=log,
    stderr=subprocess.STDOUT,
    start_new_session=True,
)
print(proc.pid)
PY
)"
  echo "$pid" > "$PID_FILE"
  wait_until_ready
  open "$URL" 2>/dev/null || true
  print_status
}

stop_server() {
  local pid
  pid="$(get_pid)"
  if [ -z "$pid" ]; then
    rm -f "$PID_FILE"
    echo "  ${DIM}Server is not running.${NC}"
    return 0
  fi

  echo -n "  Stopping ${DIM}(PID ${pid})${NC}... "
  kill "$pid" 2>/dev/null || true

  local waited=0
  while is_pid_running "$pid" && [ "$waited" -lt 20 ]; do
    sleep 0.25
    waited=$((waited + 1))
  done

  if is_pid_running "$pid"; then
    echo -n "${YELLOW}force kill${NC}... "
    kill -9 "$pid" 2>/dev/null || true
    sleep 0.25
  fi

  rm -f "$PID_FILE"
  echo "${GREEN}stopped${NC}"
}

restart_server() {
  echo ""
  echo "  ${BOLD}EasySlides${NC} -- restarting"
  stop_server
  sleep 0.5
  start_server
}

print_running_menu() {
  print_status
  if [ ! -t 0 ]; then
    echo "  ${YELLOW}Already running.${NC} Use ${BOLD}restart${NC} or ${BOLD}off${NC} explicitly."
    return 0
  fi

  echo "  ${DIM}[O]pen  [R]estart  [S]top  [Q]uit${NC}"
  echo ""
  read -r "?  > " choice
  case "$choice" in
    [oO])
      open "$URL" 2>/dev/null || true
      ;;
    [rR])
      restart_server
      ;;
    [sS])
      echo ""
      echo "  ${BOLD}EasySlides${NC} -- stopping"
      stop_server
      print_status
      ;;
    *)
      echo "  ${DIM}Cancelled.${NC}"
      ;;
  esac
}

CMD="${1:-on}"

case "$CMD" in
  on)
    start_server
    ;;
  off)
    echo ""
    echo "  ${BOLD}EasySlides${NC} -- stopping"
    stop_server
    print_status
    ;;
  restart)
    restart_server
    ;;
  status)
    print_status
    ;;
  help|-h|--help)
    print_help
    ;;
  *)
    echo "  ${RED}Unknown command: ${CMD}${NC}"
    print_help
    exit 1
    ;;
esac

exit 0
