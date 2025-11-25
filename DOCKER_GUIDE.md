# 🐳 Docker 環境セットアップガイド

このガイドでは、FitCurveをDocker環境で動かす方法を説明します。

---

## 📋 目次

1. [前提条件](#前提条件)
2. [ローカルでのDocker動作確認](#ローカルでのdocker動作確認)
3. [環境変数の設定](#環境変数の設定)
4. [Docker Composeの使い方](#docker-composeの使い方)
5. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必要なソフトウェア

- **Docker**: 20.10以上
- **Docker Compose**: 2.0以上

### インストール確認

```bash
# Dockerのバージョン確認
docker --version
# 出力例: Docker version 24.0.7, build afdd53b

# Docker Composeのバージョン確認
docker compose version
# 出力例: Docker Compose version v2.23.0
```

### Dockerのインストール（未インストールの場合）

#### Windows / Mac
- Docker Desktop: https://www.docker.com/products/docker-desktop

#### Linux (Ubuntu)
```bash
# 古いバージョンの削除
sudo apt-get remove docker docker-engine docker.io containerd runc

# 必要なパッケージのインストール
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Docker GPGキーの追加
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Dockerリポジトリの追加
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Dockerのインストール
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 現在のユーザーをdockerグループに追加（sudoなしでdockerコマンドを実行可能に）
sudo usermod -aG docker $USER

# グループ変更を反映（再ログインまたは以下のコマンド）
newgrp docker
```

---

## ローカルでのDocker動作確認

### Step 1: プロジェクトディレクトリへ移動

```bash
cd /path/to/fitCurve
```

### Step 2: 環境変数ファイルの作成

プロジェクトルートに `.env.docker` ファイルを作成：

```bash
# .env.dockerファイルを作成
cat > .env.docker << 'EOF'
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
```

### Step 3: Dockerイメージのビルド

```bash
# イメージをビルド
docker compose build

# ビルドの進行状況が表示されます（初回は5-10分程度）
```

### Step 4: コンテナの起動

```bash
# バックグラウンドで起動
docker compose up -d

# ログを表示しながら起動（デバッグ時）
docker compose up
```

### Step 5: 動作確認

#### ブラウザでアクセス

```
http://localhost:8080
```

FitCurveのホームページが表示されれば成功です！

#### ログの確認

```bash
# リアルタイムでログを表示
docker compose logs -f

# 特定のサービスのログのみ表示
docker compose logs -f fitcurve
```

#### コンテナの状態確認

```bash
# コンテナの状態を確認
docker compose ps

# 出力例:
# NAME                IMAGE               STATUS              PORTS
# fitcurve            fitcurve_fitcurve   Up 2 minutes        0.0.0.0:8080->8080/tcp
```

### Step 6: 停止と削除

```bash
# コンテナの停止
docker compose stop

# コンテナの停止と削除
docker compose down

# コンテナ、イメージ、ボリュームをすべて削除
docker compose down --rmi all --volumes
```

---

## 環境変数の設定

### 設定可能な環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `APP_ENV` | 環境（development/production） | production |
| `APP_DEBUG` | デバッグモード（true/false） | false |
| `APP_HOST` | リッスンするホスト | 0.0.0.0 |
| `APP_PORT` | ポート番号 | 8080 |
| `LOG_LEVEL` | ログレベル（DEBUG/INFO/WARNING/ERROR） | INFO |
| `MAX_UPLOAD_SIZE` | アップロードサイズ制限（MB） | 10 |
| `DEFAULT_FIT_METHOD` | デフォルトフィッティング手法 | poly |
| `DEFAULT_POLY_DEGREE` | 多項式の次数 | 3 |

### 環境変数の変更方法

1. `.env.docker` ファイルを編集
2. コンテナを再起動

```bash
# .env.dockerを編集
nano .env.docker

# コンテナを再起動
docker compose restart
```

---

## Docker Composeの使い方

### 基本コマンド

```bash
# イメージのビルド
docker compose build

# コンテナの起動
docker compose up -d

# ログの表示
docker compose logs -f

# コンテナの状態確認
docker compose ps

# コンテナの停止
docker compose stop

# コンテナの再起動
docker compose restart

# コンテナの停止と削除
docker compose down
```

### 開発時に便利なコマンド

```bash
# コンテナ内でコマンドを実行
docker compose exec fitcurve bash

# 例: コンテナ内でPythonを実行
docker compose exec fitcurve python --version

# 例: コンテナ内でテストを実行
docker compose exec fitcurve uv run pytest
```

### イメージの再ビルド

コードを変更した場合は、イメージを再ビルドしてください：

```bash
# キャッシュを使わずに再ビルド
docker compose build --no-cache

# 再ビルドして起動
docker compose up -d --build
```

---

## トラブルシューティング

### ポートが既に使用されている

**エラー例:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8080: bind: address already in use
```

**解決方法:**

#### 方法1: 使用中のポートを確認して停止

```bash
# Windowsの場合
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Macの場合
lsof -i :8080
kill -9 <PID>
```

#### 方法2: 別のポートを使用

`docker-compose.yml` を編集：

```yaml
ports:
  - "9090:8080"  # ホスト側のポートを9090に変更
```

### イメージのビルドが失敗する

**エラー例:**
```
failed to solve with frontend dockerfile.v0
```

**解決方法:**

```bash
# Docker BuildKitを無効化してビルド
DOCKER_BUILDKIT=0 docker compose build

# Dockerのリソースをクリーンアップ
docker system prune -a
```

### コンテナが起動しない

```bash
# ログを確認
docker compose logs fitcurve

# 一般的な原因:
# 1. 環境変数の設定ミス → .env.dockerを確認
# 2. ポートの競合 → docker compose ps で確認
# 3. メモリ不足 → docker stats で確認
```

### データが永続化されない

確認事項：

1. `docker-compose.yml` のボリューム設定を確認：
   ```yaml
   volumes:
     - ./data:/app/data
   ```

2. ホスト側の `data` ディレクトリが存在することを確認：
   ```bash
   ls -la data/
   ```

3. コンテナを削除する際は `--volumes` オプションに注意：
   ```bash
   # ボリュームを残して削除
   docker compose down
   
   # ボリュームも削除（データが消えます！）
   docker compose down --volumes
   ```

### Nginxプロキシを使用する場合

Nginxリバースプロキシを有効化：

```bash
# Nginxプロファイルを含めて起動
docker compose --profile with-nginx up -d
```

SSL証明書が必要です（`deploy/ssl/` に配置）。

---

## 📊 リソース使用状況の確認

```bash
# コンテナのリソース使用状況をリアルタイム表示
docker stats

# 出力例:
# CONTAINER ID   NAME       CPU %     MEM USAGE / LIMIT     MEM %
# a1b2c3d4e5f6   fitcurve   0.50%     150MiB / 4GiB        3.66%
```

---

## 🔒 セキュリティのベストプラクティス

### 1. 本番環境では必ず `APP_DEBUG=false`

```bash
# .env.dockerで確認
grep APP_DEBUG .env.docker
# 出力: APP_DEBUG=false
```

### 2. 最新のベースイメージを使用

```bash
# 定期的にイメージを更新
docker compose pull
docker compose up -d --build
```

### 3. 不要なコンテナ・イメージを削除

```bash
# 停止中のコンテナを削除
docker container prune

# 未使用のイメージを削除
docker image prune -a

# すべて削除（注意！）
docker system prune -a --volumes
```

---

## 📚 次のステップ

ローカルで動作確認ができたら、AWS EC2へのデプロイを進めましょう：

📖 **[AWS_EC2_DEPLOYMENT.md](./AWS_EC2_DEPLOYMENT.md)** - EC2デプロイガイド

---

<div align="center">

**Happy Dockerizing! 🐳**

</div>

