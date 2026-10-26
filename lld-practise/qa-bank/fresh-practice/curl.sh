#!/usr/bin/env bash
# Smoke test against a running server: ./curl.sh
set -u
BASE=${BASE:-http://localhost:8080}
curl -s -i "$BASE/health"; echo
curl -s -i -X POST "$BASE/echo" -H 'Content-Type: application/json' -d '{"hello":"world"}'; echo
curl -s -i "$BASE/hello"; echo
curl -s -i "$BASE/hello?name=Vinay"; echo
