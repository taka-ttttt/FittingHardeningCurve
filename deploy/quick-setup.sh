#!/bin/bash
# FitCurve クイックセットアップスクリプト
# 1コマンドでEC2にデプロイ

set -e

# 色付き出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== FitCurve クイックセットアップ ===${NC}"
echo ""

# GitHubリポジトリURL（必要に応じて変更）
REPO_URL="${1:-https://github.com/your-username/fitCurve.git}"

echo -e "${BLUE}1. セットアップスクリプトをダウンロード${NC}"
curl -fsSL https://raw.githubusercontent.com/your-username/fitCurve/main/deploy/setup_vps.sh -o setup.sh

echo -e "${BLUE}2. セットアップスクリプトを実行${NC}"
chmod +x setup.sh
./setup.sh "$REPO_URL"

echo -e "${GREEN}クイックセットアップ完了！${NC}"

