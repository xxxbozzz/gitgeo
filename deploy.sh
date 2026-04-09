#!/bin/bash
# ═══════════════════════════════════════════════════════
#  PCB GEO 知识引擎 — 镜像部署脚本 v4.0
#  用法: ./deploy.sh <服务器IP> [镜像Tag]
#  示例: ./deploy.sh 47.76.50.157 latest
#  示例: ./deploy.sh 47.76.50.157 sha-237b872
# ═══════════════════════════════════════════════════════

SERVER_IP=$1
IMAGE_TAG=${2:-latest}
USER="root"
REMOTE_DIR="/opt/pcb-geo-system"
IMAGE_REPO="${GEO_APP_IMAGE_REPO:-ghcr.io/xxxbozzz/pcb-geo-system}"
COMPOSE_FILE="docker-compose.prod.yml"
SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/id_geo}"
SSH_OPTS=(-o StrictHostKeyChecking=no)

if [ -f "$SSH_KEY_PATH" ]; then
    SSH_OPTS+=(-i "$SSH_KEY_PATH")
fi

SSH_TARGET="$USER@$SERVER_IP"

if [ -z "$SERVER_IP" ]; then
    echo "❌ 用法: ./deploy.sh <服务器IP> [镜像Tag]"
    exit 1
fi

if [[ "$IMAGE_TAG" == sha-* ]]; then
    GIT_COMMIT="${IMAGE_TAG#sha-}"
    GIT_COMMIT_SHORT="${IMAGE_TAG#sha-}"
    GIT_BRANCH="main"
else
    GIT_COMMIT="$IMAGE_TAG"
    GIT_COMMIT_SHORT="$IMAGE_TAG"
    GIT_BRANCH="main"
fi
GIT_DIRTY=false
DEPLOYED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TMP_BUILD_INFO=$(mktemp /tmp/pcb-geo-build.XXXXXX.json)
trap 'rm -f "$TMP_BUILD_INFO"' EXIT

cat > "$TMP_BUILD_INFO" <<EOF
{
  "git_commit": "$GIT_COMMIT",
  "git_commit_short": "$GIT_COMMIT_SHORT",
  "git_branch": "$GIT_BRANCH",
  "git_dirty": $GIT_DIRTY,
  "deployed_at": "$DEPLOYED_AT",
  "image_repo": "$IMAGE_REPO",
  "image_tag": "$IMAGE_TAG"
}
EOF

echo "🚀 PCB GEO v4.0 镜像部署到 $SERVER_IP"
echo "🧾 部署版本: $GIT_BRANCH@$GIT_COMMIT_SHORT (dirty=$GIT_DIRTY)"
echo "📦 目标镜像: $IMAGE_REPO:$IMAGE_TAG"

# ─── 1. 远程环境准备 ───
echo "📦 准备远程环境..."
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" << 'SETUP'
    # Docker 安装检查
    if ! command -v docker &> /dev/null; then
        echo "安装 Docker..."
        curl -fsSL https://get.docker.com | sh
        systemctl enable docker && systemctl start docker
    fi
    if ! docker compose version &> /dev/null; then
        echo "安装 Docker Compose..."
        apt-get update && apt-get install -y docker-compose-plugin
    fi
    if [ ! -d /opt/pcb-geo-system/.git ]; then
        git clone https://github.com/xxxbozzz/pcb-geo-system.git /opt/pcb-geo-system
    fi
    echo "✅ 环境就绪"
SETUP

# ─── 2. 拉取部署文件 ───
echo "📥 拉取最新部署文件..."
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" << 'SYNC'
    cd /opt/pcb-geo-system
    rm -f .env.image
    git checkout main
    git pull --ff-only origin main
SYNC

scp "${SSH_OPTS[@]}" "$TMP_BUILD_INFO" "$SSH_TARGET:$REMOTE_DIR/build_info.json" >/dev/null

# ─── 3. 拉镜像并启动 ───
echo "🐳 拉取镜像并启动容器..."
if [ -n "${GHCR_USERNAME:-}" ] && [ -n "${GHCR_TOKEN:-}" ]; then
    printf '%s' "$GHCR_TOKEN" | ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "docker login ghcr.io -u '$GHCR_USERNAME' --password-stdin"
else
    echo "ℹ️ 未提供 GHCR_USERNAME / GHCR_TOKEN，默认按公开镜像拉取"
fi

ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
    "IMAGE_REPO='$IMAGE_REPO' IMAGE_TAG='$IMAGE_TAG' COMPOSE_FILE='$COMPOSE_FILE' SERVER_IP='$SERVER_IP' bash -s" <<'DEPLOY'
    cd /opt/pcb-geo-system

    GEO_APP_IMAGE="$IMAGE_REPO:$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" pull backend geo-agent-app dashboard scheduler
    GEO_APP_IMAGE="$IMAGE_REPO:$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" up -d --force-recreate --no-build backend geo-agent-app dashboard scheduler

    echo "⏳ 等待 MySQL..."
    sleep 10
    for i in $(seq 1 30); do
        if docker exec geo-mysql mysqladmin ping -h localhost -u root -proot_password 2>/dev/null | grep -q alive; then
            echo "✅ MySQL 就绪"
            break
        fi
        sleep 2
    done

    echo "⏳ 执行数据库迁移..."
    docker exec geo-backend python -m alembic -c /app/backend/alembic.ini upgrade head

    echo "⏳ 检查 Backend 健康..."
    for i in $(seq 1 20); do
        if curl -fsS http://127.0.0.1:8001/api/v1/health >/dev/null 2>&1; then
            echo "✅ Backend 就绪"
            break
        fi
        sleep 2
    done

    # 检查容器状态
    echo ""
    echo "📊 容器状态:"
    GEO_APP_IMAGE="$IMAGE_REPO:$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" ps

    echo ""
    echo "═══════════════════════════════════"
    echo "  ✅ 部署完成!"
    echo "  Console V2: http://$SERVER_IP:8503/console"
    echo "  Backend API: http://$SERVER_IP:8001/api/v1"
    echo "  Legacy Dashboard: http://$SERVER_IP:8504"
    echo "═══════════════════════════════════"
DEPLOY

echo "🎉 部署完成! Console V2: http://$SERVER_IP:8503/console"
echo "🎉 Backend API: http://$SERVER_IP:8001/api/v1"
echo "🎉 旧 Dashboard 仍可访问: http://$SERVER_IP:8504"
