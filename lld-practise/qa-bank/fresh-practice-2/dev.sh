#!/usr/bin/env bash
# One entry point for a rep. Run from anywhere.
#   ./dev.sh                          run all tests, then start the server if they pass
#   ./dev.sh test                     run all tests
#   ./dev.sh test HelloWorldControllerTest   run one class (or Class#method)
#   ./dev.sh run                      start the server on :8080 (Ctrl+C stops it)
#   ./dev.sh smoke                    curl the running server (runs ./curl.sh)
set -euo pipefail
cd "$(dirname "$0")"
PORT=${PORT:-8080}

# Fail fast with the PID instead of a long Spring stack trace when the port is taken.
check_port_free() {
  local pid
  pid=$(lsof -nP -tiTCP:"$PORT" -sTCP:LISTEN || true)
  if [[ -n "$pid" ]]; then
    echo "Port $PORT is already in use by PID $pid ($(ps -o comm= -p "$pid")). Stop it: kill $pid" >&2
    exit 1
  fi
}

run_tests() {
  if [[ $# -gt 0 ]]; then mvn test -Dtest="$1"; else mvn test; fi
}

run_server() {
  check_port_free
  mvn spring-boot:run -Dspring-boot.run.arguments=--server.port="$PORT"
}

case "${1:-all}" in
  all)   run_tests && run_server ;;
  test)  shift; run_tests "$@" ;;
  run)   run_server ;;
  smoke) BASE="http://localhost:$PORT" ./curl.sh ;;
  *)     sed -n '3,7p' "$0"; exit 1 ;;
esac
