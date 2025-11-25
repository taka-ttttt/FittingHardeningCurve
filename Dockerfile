FROM python:3.12-slim

# 作業ディレクトリ
WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uvのインストール
ENV PATH="/root/.local/bin:${PATH}"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# アプリケーションファイルのコピー
COPY pyproject.toml uv.lock ./
COPY app/ ./app/
COPY scripts/ ./scripts/

# 依存関係のインストール
RUN uv sync --frozen

# データディレクトリの作成
RUN mkdir -p data/uploads data/fits data/cache

# 環境変数
ENV APP_ENV=production
ENV APP_DEBUG=false
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8080

# ポート公開
EXPOSE 8080

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')"

# アプリケーション起動
CMD ["uv", "run", "python", "app/main.py"]


