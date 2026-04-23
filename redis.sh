#!/usr/bin/env bash

set -euo pipefail

container_name="${REDIS_CONTAINER_NAME:-redis-broker}"
image="${REDIS_IMAGE:-redis:7-alpine}"
mode="${REDIS_MODE:-persistent}"

if docker container inspect "$container_name" >/dev/null 2>&1; then
  current_state="$(docker inspect -f '{{.State.Status}}' "$container_name")"

  if [[ "$current_state" == "running" ]]; then
    echo "$container_name is already running"
    exit 0
  fi

  docker start "$container_name" >/dev/null
  echo "Started existing $container_name"
  exit 0
fi

if [[ "$mode" == "quick" ]]; then
  docker run -d --name "$container_name" -p 6379:6379 "$image"
else
  docker run -d \
    --name "$container_name" \
    -p 6379:6379 \
    --restart unless-stopped \
    -v redis_data:/data \
    "$image" \
    redis-server --appendonly yes
fi

echo "Created $container_name"