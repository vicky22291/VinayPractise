#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v mvn >/dev/null 2>&1; then
    echo "Maven is required. Install Maven and a JDK 21 or newer, then retry." >&2
    exit 1
fi

exec mvn --batch-mode spring-boot:run "$@"
