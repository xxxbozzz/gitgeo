#!/bin/bash

set -euo pipefail

SERVER_IP=${1:-}
USER="root"
SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/id_geo}"
SSH_OPTS=(-o StrictHostKeyChecking=no)

if [ -f "$SSH_KEY_PATH" ]; then
    SSH_OPTS+=(-i "$SSH_KEY_PATH")
fi

if [ -z "$SERVER_IP" ]; then
    echo "用法: ./scripts/remote_docker_cleanup.sh <服务器IP>"
    exit 1
fi

SSH_TARGET="$USER@$SERVER_IP"

echo "== 清理前占用 =="
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" 'docker system df'

echo
echo "== 清理未使用镜像 =="
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" 'docker image prune -f'

echo
echo "== 清理构建缓存 =="
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" 'docker builder prune -f'

echo
echo "== 清理后占用 =="
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" 'docker system df'
