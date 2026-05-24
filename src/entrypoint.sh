#!/bin/bash
set -euo pipefail
wait_host() {
  local host="$1" port="$2"
  until nc -z "$host" "$port"; do sleep 1; done
}
wait_host "${MONGO_HOST:-taxi-mongo}" "${MONGO_PORT:-27017}"
wait_host "${REDIS_HOST:-taxi-redis}" "${REDIS_PORT:-6379}"
exec python -m bin
