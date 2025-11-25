#!/bin/bash
# FittingHardeningCurve EC2 セットアップスクリプト（Docker版）
# Ubuntu 22.04用

set -e

echo "=== FittingHardeningCurve EC2 Docker セットアップ開始 ==="

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 変数
GITHUB_REPO="${1:-https://github.com/taka-ttttt/FittingHardeningCurve.git}"
INSTALL_DIR="$HOME/FittingHardeningCurve"

echo -e "${BLUE}=== 環境情報 ===${NC}"
echo "OS: $(lsb_release -ds)"
echo "ユーザー: $(whoami)"
echo "ホームディレクトリ: $HOME"
echo ""

# ============================================
# 1. システムの更新
# ============================================
echo -e "${GREEN}[1/7] システムの更新${NC}"
sudo apt update
sudo apt upgrade -y

# ============================================
# 2. 必要なパッケージのインストール
# ============================================
echo -e "${GREEN}[2/7] 必要なパッケージのインストール${NC}"
sudo apt install -y \
    curl \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    htop \
    vim

# ============================================
# 3. Dockerのインストール
# ============================================
echo -e "${GREEN}[3/7] Dockerのインストール${NC}"

if command -v docker &> /dev/null; then
    echo -e "${YELLOW}Dockerは既にインストールされています${NC}"
    docker --version
else
    echo "Dockerをインストールしています..."
    
    # Dockerの公式GPGキーを追加
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Dockerリポジトリの追加
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Dockerのインストール
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # 現在のユーザーをdockerグループに追加
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}Dockerのインストールが完了しました${NC}"
    docker --version
fi

# ============================================
# 4. リポジトリのクローン
# ============================================
echo -e "${GREEN}[4/7] リポジトリのクローン${NC}"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}ディレクトリ $INSTALL_DIR は既に存在します${NC}"
    echo "最新の変更を取得しています..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "リポジトリをクローンしています..."
    git clone "$GITHUB_REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ============================================
# 5. 環境変数の設定
# ============================================
echo -e "${GREEN}[5/7] 環境変数の設定${NC}"

if [ ! -f "$INSTALL_DIR/.env.docker" ]; then
    cat > "$INSTALL_DIR/.env.docker" << 'EOF'
# アプリケーション設定
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8080

# ログ設定
LOG_LEVEL=INFO

# ファイルアップロード制限（MB）
MAX_UPLOAD_SIZE=10

# デフォルトフィッティング設定
DEFAULT_FIT_METHOD=poly
DEFAULT_POLY_DEGREE=3
EOF
    echo -e "${GREEN}.env.docker ファイルを作成しました${NC}"
else
    echo -e "${YELLOW}.env.docker ファイルは既に存在します${NC}"
fi

# ============================================
# 6. データディレクトリの作成
# ============================================
echo -e "${GREEN}[6/7] データディレクトリの作成${NC}"
mkdir -p "$INSTALL_DIR/data/uploads" "$INSTALL_DIR/data/fits" "$INSTALL_DIR/data/cache"
chmod -R 755 "$INSTALL_DIR/data"

# ============================================
# 7. Dockerコンテナの起動
# ============================================
echo -e "${GREEN}[7/7] Dockerコンテナの起動${NC}"

# Dockerグループの変更を反映するため、新しいシェルで実行
if groups | grep -q docker; then
    echo "Dockerイメージをビルドしています（初回は5-10分かかります）..."
    docker compose build
    
    echo "コンテナを起動しています..."
    docker compose up -d
    
    echo -e "${GREEN}コンテナの起動が完了しました${NC}"
else
    echo -e "${YELLOW}注意: Dockerグループの変更を反映するため、以下のコマンドを実行してください:${NC}"
    echo ""
    echo "  newgrp docker"
    echo "  cd $INSTALL_DIR"
    echo "  docker compose build"
    echo "  docker compose up -d"
    echo ""
fi

# ============================================
# セットアップ完了
# ============================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  FittingHardeningCurve セットアップ完了！ 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# IPアドレスの取得
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || echo "Unknown")
PRIVATE_IP=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}=== アクセス情報 ===${NC}"
echo "パブリックIP: $PUBLIC_IP"
echo "プライベートIP: $PRIVATE_IP"
echo ""
echo "以下のURLでアクセスできます:"
echo "  http://$PUBLIC_IP:8080"
echo ""

echo -e "${BLUE}=== 次のステップ ===${NC}"
echo ""
echo "1. セキュリティグループの確認:"
echo "   AWS EC2コンソールでポート8080が開いているか確認"
echo ""
echo "2. アプリケーションの動作確認:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo ""
echo "3. SSL証明書の設定（オプション）:"
echo "   詳細は AWS_EC2_DEPLOYMENT.md を参照"
echo ""
echo "4. 自動起動の設定:"
echo "   sudo systemctl enable docker"
echo ""
echo "5. 監視:"
echo "   docker stats"
echo "   docker compose logs -f"
echo ""

echo -e "${YELLOW}=== トラブルシューティング ===${NC}"
echo ""
echo "コンテナの状態確認:"
echo "  cd $INSTALL_DIR"
echo "  docker compose ps"
echo ""
echo "ログの確認:"
echo "  docker compose logs -f fitcurve"
echo ""
echo "コンテナの再起動:"
echo "  docker compose restart"
echo ""
echo "完全な再ビルド:"
echo "  docker compose down"
echo "  docker compose build --no-cache"
echo "  docker compose up -d"
echo ""

echo -e "${GREEN}詳細なドキュメント:${NC}"
echo "  - Docker環境: $INSTALL_DIR/DOCKER_GUIDE.md"
echo "  - EC2デプロイ: $INSTALL_DIR/AWS_EC2_DEPLOYMENT.md"
echo ""
echo -e "${GREEN}セットアップスクリプト完了！${NC}"


