#!/usr/bin/env bash
# Smoke test against a running server: ./curl.sh
set -u
BASE=${BASE:-http://localhost:8080}
curl -s -i "$BASE/hello"; echo
curl -s -i "$BASE/hello?name=Vinay"; echo
