# ☁️ AWS EC2 デプロイメントガイド

このガイドでは、FitCurveをAWS EC2上でDockerを使ってデプロイする方法を詳しく説明します。

---

## 📋 目次

1. [前提条件](#前提条件)
2. [AWS EC2インスタンスの作成](#aws-ec2インスタンスの作成)
3. [セキュリティグループの設定](#セキュリティグループの設定)
4. [SSH接続とサーバーセットアップ](#ssh接続とサーバーセットアップ)
5. [Dockerのインストール](#dockerのインストール)
6. [アプリケーションのデプロイ](#アプリケーションのデプロイ)
7. [ドメイン設定（オプション）](#ドメイン設定オプション)
8. [SSL証明書の設定（Let's Encrypt）](#ssl証明書の設定lets-encrypt)
9. [自動起動の設定](#自動起動の設定)
10. [監視とメンテナンス](#監視とメンテナンス)
11. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必要なもの

- ✅ **AWSアカウント** - https://aws.amazon.com/
- ✅ **SSH鍵ペア** - EC2インスタンスへの接続用
- ✅ **ドメイン名**（オプション） - 独自ドメインを使用する場合
- ✅ **基本的なLinuxコマンドの知識**

### 推奨スペック

| 項目 | 最小 | 推奨 |
|------|------|------|
| **インスタンスタイプ** | t2.micro (1 vCPU, 1GB RAM) | t3.small (2 vCPU, 2GB RAM) |
| **ストレージ** | 8GB | 20GB以上 |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### 月額料金目安

- **t2.micro**: $0/月（無料枠の場合）〜 $8/月
- **t3.small**: 約 $15/月
- **データ転送**: 1GB/月まで無料、以降約$0.09/GB

---

## AWS EC2インスタンスの作成

### Step 1: AWSコンソールへログイン

1. https://console.aws.amazon.com/ にアクセス
2. AWSアカウントでログイン

### Step 2: EC2ダッシュボードへ移動

1. サービスメニューから「EC2」を選択
2. リージョンを選択（例: アジアパシフィック（東京）ap-northeast-1）

### Step 3: インスタンスの起動

#### 1. 「インスタンスを起動」ボタンをクリック

#### 2. インスタンス設定

**名前とタグ:**
```
名前: fitcurve-production
```

**アプリケーションおよびOSイメージ (Amazon Machine Image):**
- **クイックスタート**: Ubuntu
- **AMI**: Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
- **アーキテクチャ**: 64ビット (x86)

**インスタンスタイプ:**
```
t3.small（推奨）または t2.micro（無料枠）
```

**キーペア (ログイン):**
- 既存のキーペアを選択、または
- 「新しいキーペアの作成」をクリック
  - キーペア名: `fitcurve-key`
  - キーペアタイプ: RSA
  - プライベートキーファイル形式: `.pem`
  - **ダウンロードしたキーペアは安全に保管してください！**

**ネットワーク設定:**
- VPC: デフォルト
- サブネット: デフォルト
- パブリックIPの自動割り当て: 有効

**ファイアウォール (セキュリティグループ):**
- 「セキュリティグループを作成」を選択
- セキュリティグループ名: `fitcurve-sg`
- 説明: `Security group for FitCurve application`

**ストレージを設定:**
```
サイズ: 20 GiB（推奨）
ボリュームタイプ: gp3（汎用SSD）
```

#### 3. インスタンスの起動

右下の「インスタンスを起動」ボタンをクリック

### Step 4: インスタンスの起動確認

1. 「インスタンス」ページに移動
2. 新しいインスタンスのステータスが「実行中」になるまで待機（約1-2分）
3. インスタンスのパブリックIPアドレスをメモ
   - 例: `52.192.123.45`

---

## セキュリティグループの設定

EC2インスタンスへのアクセスを制御します。

### Step 1: セキュリティグループの編集

1. EC2ダッシュボードで「セキュリティグループ」を選択
2. `fitcurve-sg` を選択
3. 「インバウンドルール」タブを選択
4. 「インバウンドルールを編集」をクリック

### Step 2: 必要なルールの追加

以下のルールを追加してください：

| タイプ | プロトコル | ポート範囲 | ソース | 説明 |
|--------|-----------|-----------|--------|------|
| SSH | TCP | 22 | マイIP | SSH接続用 |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP接続用 |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS接続用 |
| カスタムTCP | TCP | 8080 | 0.0.0.0/0 | アプリ直接接続（テスト用・後で削除） |

**重要:** 
- **SSH（ポート22）** は必ず「マイIP」に制限してください
- 本番運用時は **8080ポートのルールは削除** してください（Nginxを経由させるため）

### Step 3: ルールの保存

「ルールを保存」をクリック

---

## SSH接続とサーバーセットアップ

### Step 1: SSH鍵の準備

#### Windows（PowerShellまたはコマンドプロンプト）

```powershell
# ダウンロードしたキーファイルを適切な場所に配置
# 例: C:\Users\YourName\.ssh\fitcurve-key.pem
```

#### Mac / Linux

```bash
# ダウンロードしたキーファイルを ~/.ssh/ に配置
mv ~/Downloads/fitcurve-key.pem ~/.ssh/

# キーファイルの権限を変更（重要！）
chmod 400 ~/.ssh/fitcurve-key.pem
```

### Step 2: SSH接続

```bash
# EC2インスタンスに接続
ssh -i ~/.ssh/fitcurve-key.pem ubuntu@<EC2のパブリックIP>

# 例:
ssh -i ~/.ssh/fitcurve-key.pem ubuntu@52.192.123.45

# 初回接続時に「Are you sure you want to continue connecting?」と聞かれたら「yes」
```

接続成功すると、以下のようなプロンプトが表示されます：

```
ubuntu@ip-172-31-xx-xx:~$
```

### Step 3: システムの更新

```bash
# パッケージリストの更新
sudo apt update

# インストール済みパッケージのアップグレード
sudo apt upgrade -y

# 再起動が必要な場合は再起動
sudo reboot
# 再起動後、再度SSH接続してください
```

---

## Dockerのインストール

### 自動インストールスクリプトを使用

```bash
# Dockerの公式インストールスクリプトをダウンロードして実行
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER

# グループ変更を反映（以下のいずれかを実行）
# 方法1: 新しいシェルを起動
newgrp docker

# 方法2: 再ログイン
exit
ssh -i ~/.ssh/fitcurve-key.pem ubuntu@<EC2のパブリックIP>
```

### インストール確認

```bash
# Dockerのバージョン確認
docker --version
# 出力例: Docker version 24.0.7, build afdd53b

# Docker Composeのバージョン確認
docker compose version
# 出力例: Docker Compose version v2.23.0

# Dockerの動作確認
docker run hello-world
# "Hello from Docker!" と表示されれば成功
```

---

## アプリケーションのデプロイ

### Step 1: リポジトリのクローン

```bash
# ホームディレクトリに移動
cd ~

# Gitのインストール（まだの場合）
sudo apt install -y git

# リポジトリをクローン
git clone https://github.com/your-username/fitCurve.git

# プロジェクトディレクトリに移動
cd fitCurve
```

### Step 2: 環境変数の設定

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

# ファイルの内容を確認
cat .env.docker
```

### Step 3: データディレクトリの作成

```bash
# データディレクトリを作成
mkdir -p data/uploads data/fits data/cache

# 権限の設定
chmod -R 755 data/
```

### Step 4: Dockerイメージのビルド

```bash
# イメージをビルド（初回は5-10分程度かかります）
docker compose build

# ビルドの進行状況が表示されます
```

### Step 5: コンテナの起動

```bash
# バックグラウンドでコンテナを起動
docker compose up -d

# 起動ログを確認
docker compose logs -f

# Ctrl+C でログ表示を終了
```

### Step 6: 動作確認

#### ブラウザでアクセス

```
http://<EC2のパブリックIP>:8080

例: http://52.192.123.45:8080
```

FitCurveのホームページが表示されれば成功です！🎉

#### コンテナの状態確認

```bash
# コンテナの状態を確認
docker compose ps

# ログを確認
docker compose logs -f fitcurve
```

---

## ドメイン設定（オプション）

独自ドメインを使用する場合の設定です。

### Step 1: ドメインの取得

お名前.com、AWS Route 53、Google Domainsなどでドメインを取得

### Step 2: DNSレコードの設定

ドメインのDNS設定で、以下のAレコードを追加：

```
タイプ: A
名前: @ または fitcurve
値: <EC2のパブリックIP>
TTL: 300（5分）
```

例:
```
fitcurve.example.com → 52.192.123.45
```

### Step 3: Elastic IPの割り当て（推奨）

EC2インスタンスを再起動するとパブリックIPが変わるため、Elastic IPを使用することを推奨します。

#### Elastic IPの作成

1. EC2ダッシュボードで「Elastic IP」を選択
2. 「Elastic IPアドレスを割り当てる」をクリック
3. 「割り当て」をクリック

#### Elastic IPの関連付け

1. 作成したElastic IPを選択
2. 「アクション」→「Elastic IPアドレスの関連付け」
3. インスタンス: `fitcurve-production` を選択
4. 「関連付け」をクリック

#### DNSレコードの更新

Elastic IPアドレスでDNSレコードを更新してください。

---

## SSL証明書の設定（Let's Encrypt）

無料のSSL証明書を取得してHTTPS化します。

### 前提条件

- ドメインが設定されていること
- DNSレコードが正しく設定されていること（伝播に最大48時間かかる場合あり）

### Step 1: Certbotのインストール

```bash
# Certbotのインストール
sudo apt install -y certbot
```

### Step 2: スタンドアロンモードで証明書を取得

```bash
# FitCurveコンテナを一時停止（80ポートを空けるため）
cd ~/fitCurve
docker compose stop

# 証明書を取得
sudo certbot certonly --standalone -d your-domain.com

# 例:
sudo certbot certonly --standalone -d fitcurve.example.com

# プロンプトに従って入力:
# - メールアドレス: あなたのメールアドレス
# - 利用規約: A (Agree)
# - メール受信: Y (はい) または N (いいえ)
```

証明書が `/etc/letsencrypt/live/your-domain.com/` に保存されます。

### Step 3: SSL証明書をDockerボリュームにコピー

```bash
# SSLディレクトリを作成
mkdir -p ~/fitCurve/deploy/ssl

# 証明書をコピー
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ~/fitCurve/deploy/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ~/fitCurve/deploy/ssl/

# 権限の設定
sudo chown -R $USER:$USER ~/fitCurve/deploy/ssl
chmod 644 ~/fitCurve/deploy/ssl/*.pem
```

### Step 4: Nginxプロファイルで起動

```bash
# Nginxリバースプロキシを含めて起動
cd ~/fitCurve
docker compose --profile with-nginx up -d

# ログを確認
docker compose logs -f
```

### Step 5: 動作確認

```
https://your-domain.com

例: https://fitcurve.example.com
```

HTTPSで接続できれば成功です！🔒

### Step 6: 証明書の自動更新設定

Let's Encrypt証明書は90日で期限切れになるため、自動更新を設定します。

```bash
# crontabを編集
crontab -e

# エディタが開いたら、以下を追加（毎日午前3時に更新チェック）
0 3 * * * sudo certbot renew --quiet --deploy-hook "cd ~/fitCurve && docker compose restart nginx"

# 保存して終了（nano: Ctrl+X, Y, Enter）
```

---

## 自動起動の設定

EC2インスタンスの再起動時に自動的にDockerコンテナが起動するように設定します。

### 方法1: Docker Composeの再起動ポリシー（既に設定済み）

`docker-compose.yml` に `restart: always` が設定されているため、Docker自体が起動すれば自動的にコンテナも起動します。

### 方法2: Systemdサービスの作成（より確実）

```bash
# サービスファイルを作成
sudo tee /etc/systemd/system/fitcurve.service > /dev/null << 'EOF'
[Unit]
Description=FitCurve Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/fitCurve
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# サービスを有効化
sudo systemctl enable fitcurve.service

# サービスを開始
sudo systemctl start fitcurve.service

# サービスの状態確認
sudo systemctl status fitcurve.service
```

### 動作確認

```bash
# EC2インスタンスを再起動
sudo reboot

# 再起動後、再度SSH接続
ssh -i ~/.ssh/fitcurve-key.pem ubuntu@<EC2のパブリックIP>

# コンテナが自動起動しているか確認
docker compose ps
```

---

## 監視とメンテナンス

### ログの確認

```bash
# リアルタイムでログを表示
docker compose logs -f

# 過去100行のログを表示
docker compose logs --tail=100

# 特定のサービスのログのみ
docker compose logs -f fitcurve
```

### リソース使用状況の確認

```bash
# Dockerコンテナのリソース使用状況
docker stats

# システム全体のリソース
htop  # インストール: sudo apt install htop
```

### ディスク使用量の確認

```bash
# ディスク使用量
df -h

# Dockerのディスク使用量
docker system df

# 不要なDockerオブジェクトを削除
docker system prune -a
```

### アプリケーションの更新

```bash
# 最新のコードを取得
cd ~/fitCurve
git pull origin main

# イメージを再ビルド
docker compose build

# コンテナを再起動
docker compose up -d --force-recreate

# 古いイメージを削除
docker image prune
```

### バックアップ

```bash
# データディレクトリをバックアップ
tar -czf fitcurve-data-$(date +%Y%m%d).tar.gz ~/fitCurve/data/

# バックアップをS3にアップロード（AWS CLIインストール後）
aws s3 cp fitcurve-data-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

---

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker compose logs fitcurve

# コンテナの詳細情報を確認
docker compose ps -a

# イメージを再ビルド
docker compose build --no-cache
docker compose up -d
```

### アプリケーションにアクセスできない

#### 1. セキュリティグループの確認

- ポート80, 443, 8080が開いているか確認

#### 2. コンテナの状態確認

```bash
docker compose ps
# STATUSが"Up"になっているか確認
```

#### 3. ポートのリッスン確認

```bash
# 8080ポートがリッスンされているか確認
sudo netstat -tlnp | grep 8080

# Dockerコンテナからのアクセステスト
curl http://localhost:8080
```

### SSL証明書の更新に失敗する

```bash
# Certbotのログを確認
sudo cat /var/log/letsencrypt/letsencrypt.log

# 手動で更新を試行
sudo certbot renew --dry-run

# 証明書を再取得
sudo certbot certonly --standalone -d your-domain.com --force-renewal
```

### メモリ不足

```bash
# スワップファイルを作成（t2.microの場合推奨）
sudo dd if=/dev/zero of=/swapfile bs=1G count=2
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永続化
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Dockerのネットワークエラー

```bash
# Dockerのネットワークをリセット
docker compose down
docker network prune
docker compose up -d
```

---

## 📊 推奨構成

### 小規模利用（個人・デモ）

```
インスタンスタイプ: t2.micro または t3.small
ストレージ: 20GB
月額コスト: 無料〜$15
```

### 中規模利用（チーム・部門）

```
インスタンスタイプ: t3.medium
ストレージ: 50GB
ロードバランサー: Application Load Balancer
月額コスト: $30〜$50
```

### 大規模利用（企業）

```
インスタンスタイプ: t3.large以上
ストレージ: 100GB以上
RDS: PostgreSQL（データの永続化）
S3: ファイルストレージ
CloudWatch: 監視
Auto Scaling: 負荷に応じたスケーリング
月額コスト: $100〜
```

---

## 🔒 セキュリティチェックリスト

- [ ] SSH接続はキーペア認証のみ（パスワード認証無効）
- [ ] セキュリティグループでSSHはマイIPのみ許可
- [ ] 本番環境で `APP_DEBUG=false` に設定
- [ ] SSL証明書を設定（HTTPS化）
- [ ] 定期的なセキュリティアップデート
- [ ] バックアップの定期実行
- [ ] CloudWatch等で監視設定
- [ ] IAMロールで適切なアクセス制御

---

## 📞 サポートリソース

### AWS公式ドキュメント
- EC2ユーザーガイド: https://docs.aws.amazon.com/ec2/
- VPCユーザーガイド: https://docs.aws.amazon.com/vpc/

### Docker公式ドキュメント
- Docker Docs: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/

### Let's Encrypt
- Certbot: https://certbot.eff.org/

---

## 💰 コスト削減のヒント

1. **無料枠の活用**: 新規アカウントは12ヶ月間t2.microが無料
2. **インスタンスの停止**: 使用しない時間帯は停止（EBSストレージ代のみ課金）
3. **リザーブドインスタンス**: 長期利用の場合は最大75%割引
4. **スポットインスタンス**: 最大90%割引（可用性に注意）

---

<div align="center">

**デプロイ完了！おめでとうございます！🎉**

FitCurveがAWS EC2上で稼働中です。

</div>

