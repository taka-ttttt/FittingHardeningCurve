# FitCurve - カーブフィッティングツール

<div align="center">

NiceGUIとPlotlyを使用した、モダンで拡張性の高いカーブフィッティングWebアプリケーション

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 📖 目次

- [概要](#概要)
- [主な機能](#主な機能)
- [クイックスタート](#クイックスタート)
- [技術スタック](#技術スタック)
- [プロジェクト構造](#プロジェクト構造)
- [アーキテクチャの特徴](#アーキテクチャの特徴)
- [使い方](#使い方)
- [開発](#開発)
- [今後の拡張](#今後の拡張)
- [ライセンス](#ライセンス)

---

## 概要

FitCurveは、科学技術計算やデータ分析のためのカーブフィッティングツールです。直感的なWebインターフェースと堅牢なアーキテクチャにより、簡単かつ正確なデータ解析を実現します。

### ✨ なぜFitCurve？

- 🎨 **モダンなUI**: NiceGUI + Quasarコンポーネントによる美しいインターフェース
- 🔧 **拡張性**: Registryパターンにより新しいモデルの追加が容易
- 📊 **インタラクティブ**: Plotlyによるリアルタイムなグラフ操作
- 🏗️ **堅牢な設計**: レイヤードアーキテクチャによる保守性の高いコード
- 🧪 **テスト済み**: pytest + Pydanticによる型安全な実装

---

## 主な機能

### データ管理
- ✅ **CSVアップロード**: ドラッグ&ドロップ対応
- ✅ **自動エンコーディング検出**: UTF-8, Shift-JIS, CP932に対応
- ✅ **データプレビュー**: アップロード前に内容を確認
- ✅ **データバリデーション**: 異常値の自動検出

### フィッティングモデル
- 📐 **多項式フィット**: 1〜10次の任意の次数
- 📈 **指数関数フィット**: y = a·e^(bx) + c
- 📉 **対数関数フィット**: y = a + b·ln(x)
- 🔢 **べき乗関数フィット**: y = a·x^b
- 🔩 **材料力学モデル**: Ludwik, Swift, Voce

### 統計分析
- 📊 **適合度評価**: R²（決定係数）
- 📏 **誤差指標**: RMSE, MAE
- 📈 **情報量規準**: AIC, BIC
- 🎯 **残差分析**: 散布図 + ヒストグラム

### 可視化・エクスポート
- 🎨 **Plotlyグラフ**: ズーム、パン、ホバー情報
- 💾 **結果保存**: JSON, CSV, テキストレポート
- 🖼️ **画像エクスポート**: PNG, SVG形式（予定）
- 📂 **履歴管理**: 過去のフィッティング結果を管理

---

## クイックスタート

### 必要要件

- Python 3.12以上
- uv (パッケージマネージャー)

### インストール

```bash
# 1. リポジトリのクローン
git clone https://github.com/taka-ttttt/fitCurve.git
cd fitCurve

# 2. 依存関係のインストール
uv sync

# 3. 環境設定（オプション）
cp .env.example .env

# 4. サンプルデータ生成（任意）
uv run python scripts/make_sample_csv.py
```

### アプリケーションの起動

#### ローカル開発環境

```bash
uv run python app/main.py
```

ブラウザで **http://localhost:5173** にアクセスしてください。

#### Docker環境（推奨）

```bash
# 環境変数ファイルの作成
cat > .env.docker << 'EOF'
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8080
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=10
DEFAULT_FIT_METHOD=poly
DEFAULT_POLY_DEGREE=3
EOF

# Dockerイメージのビルドと起動
docker compose build
docker compose up -d

# ブラウザでアクセス
# http://localhost:8080
```

詳細は **[DOCKER_GUIDE.md](./DOCKER_GUIDE.md)** を参照してください。

### 🌐 AWS EC2にデプロイする

本番環境でFitCurveをインターネット上に公開する場合：

#### クイックスタート（3ステップ）

```bash
# 1. EC2インスタンスに接続
ssh -i your-key.pem ubuntu@your-ec2-ip

# 2. セットアップスクリプトを実行
bash <(curl -fsSL https://raw.githubusercontent.com/taka-ttttt/fitCurve/main/deploy/setup_vps.sh)

# 3. ブラウザでアクセス
# http://your-ec2-ip:8080
```

#### 詳細な手順

- 📖 **[Docker環境セットアップ](./DOCKER_GUIDE.md)** - ローカルでのDocker動作確認
- 🚀 **[AWS EC2デプロイガイド](./AWS_EC2_DEPLOYMENT.md)** - 本番環境への完全デプロイ手順

---

## 技術スタック

| カテゴリ | 技術 | バージョン |
|---------|------|-----------|
| **UIフレームワーク** | NiceGUI | 3.0+ |
| **データ可視化** | Plotly | 6.3+ |
| **数値計算** | NumPy | 2.0+ |
| **数値計算** | SciPy | 1.16+ |
| **データ処理** | Pandas | 2.3+ |
| **モデル管理** | Pydantic | 2.0+ |
| **設定管理** | Pydantic-settings | 2.0+ |
| **テスト** | pytest | 8.0+ |
| **パッケージ管理** | uv | - |
| **コンテナ** | Docker | 20.10+ |
| **インフラ** | AWS EC2 | Ubuntu 22.04 |

---

## プロジェクト構造

```
fitcurve/
├── app/
│   ├── main.py                    # アプリケーションエントリポイント
│   ├── settings.py                # 設定管理（Pydantic-settings）
│   ├── logging_conf.py            # ログ設定
│   │
│   ├── core/                      # ビジネスロジック層（UI非依存）
│   │   ├── models/                # データモデル（Pydantic）
│   │   │   ├── dataset.py         # Dataset, DatasetMetadata
│   │   │   ├── fit_request.py     # FitConfig, FitRequest
│   │   │   └── fit_result.py      # FitResult, FitStatistics
│   │   │
│   │   ├── fitting/               # フィッティングエンジン
│   │   │   ├── registry.py        # FitterRegistry（動的管理）
│   │   │   ├── base.py            # BaseFitter（抽象基底クラス）
│   │   │   ├── poly.py            # PolynomialFitter
│   │   │   ├── exp.py             # ExponentialFitter
│   │   │   ├── log.py             # LogarithmicFitter
│   │   │   ├── power.py           # PowerFitter
│   │   │   ├── ludwik.py          # LudwikFitter
│   │   │   ├── swift.py           # SwiftFitter
│   │   │   └── voce.py            # VoceFitter
│   │   │
│   │   ├── services/              # サービス層
│   │   │   ├── datasets.py        # DatasetService（データ管理）
│   │   │   ├── fitting.py         # FittingService（フィット実行）
│   │   │   ├── preprocessing.py   # PreprocessingService
│   │   │   └── exports.py         # ExportService（結果出力）
│   │   │
│   │   ├── utils/                 # ユーティリティ
│   │   │   ├── fileio.py          # ファイル操作
│   │   │   ├── stats.py           # 統計計算
│   │   │   └── monitoring.py      # パフォーマンス監視
│   │   │
│   │   └── exceptions.py          # カスタム例外定義
│   │
│   ├── ui/                        # UI層（NiceGUI）
│   │   ├── layout.py              # 共通レイアウト（ヘッダー、フッター）
│   │   │
│   │   ├── components/            # 再利用可能なコンポーネント
│   │   │   ├── charts.py          # Plotlyグラフコンポーネント
│   │   │   └── file_table.py      # データテーブル
│   │   │
│   │   └── pages/                 # ページ実装
│   │       ├── home.py            # ホームページ
│   │       ├── upload.py          # データアップロード
│   │       ├── fit.py             # フィッティング実行
│   │       └── results.py         # 結果管理
│   │
│   └── tests/                     # テストコード（pytest）
│       ├── conftest.py            # フィクスチャ定義
│       ├── test_fitting.py        # フィッティングテスト
│       ├── test_models.py         # モデルテスト
│       └── test_utils.py          # ユーティリティテスト
│
├── data/                          # 実行時データ（.gitignore）
│   ├── uploads/                   # アップロードされたCSV
│   ├── fits/                      # フィッティング結果
│   └── cache/                     # 一時キャッシュ
│
├── scripts/
│   └── make_sample_csv.py         # サンプルデータ生成
│
├── pyproject.toml                 # プロジェクト設定
├── uv.lock                        # 依存関係ロックファイル
├── .gitignore
├── .env.example                   # 環境変数テンプレート
└── README.md
```

---

## アーキテクチャの特徴

FitCurveは、モダンなWebアプリケーション開発のベストプラクティスに基づいて設計されています。

### 1. 🏭 Registryパターン

新しいフィッティング手法の追加が**わずか1行**で可能です。

#### メリット
- ✅ Open-Closed原則に準拠（拡張に開き、修正に閉じる）
- ✅ コード量を**84%削減**（19行 → 3行）
- ✅ 利用可能なメソッド一覧の動的取得

#### 実装例

**Before（19行のif-elif）:**
```python
def create_fitter(self, config: FitConfig) -> BaseFitter:
    if method == "ludwik":
        return LudwikFitter(config)
    elif method == "swift":
        return SwiftFitter(config)
    # ... 繰り返し
```

**After（3行）:**
```python
def create_fitter(self, config: FitConfig) -> BaseFitter:
    return FitterRegistry.create(config)
```

#### 新規モデルの追加方法

```python
# 1. フィッタークラスを作成（app/core/fitting/new_method.py）
class NewMethodFitter(BaseFitter):
    def fit(self) -> FitResult:
        # 実装
        pass

# 2. Registryに登録（app/core/fitting/__init__.py）
FitterRegistry.register("new_method", NewMethodFitter)

# 3. 型定義に追加（app/core/models/fit_request.py）
FitMethod = Literal["...", "new_method"]
```

**以上！既存コードの変更は不要です。**

---

### 2. 🛡️ カスタム例外システム

エラーの種類を明確に区別し、適切なハンドリングが可能です。

| 例外クラス | 用途 |
|-----------|------|
| `FitCurveException` | ベース例外 |
| `DataValidationError` | データバリデーションエラー |
| `FittingError` | フィッティング実行エラー |
| `DatasetNotFoundError` | データセット未検出 |
| `FileOperationError` | ファイル操作エラー |
| `ConfigurationError` | 設定エラー |

#### 使用例

```python
try:
    result = fitting_service.execute_fit(dataset, request)
except DataValidationError as e:
    logger.warning(f"データが不正です: {e}")
    # ユーザーに入力修正を促す
except FittingError as e:
    logger.error(f"フィッティングに失敗しました: {e}")
    # 別のモデルを試す
```

---

### 3. ⏱️ パフォーマンス監視

`@performance_monitor` デコレータで関数の実行時間を自動計測します。

#### 機能
- ✅ 実行時間の自動計測
- ✅ 実行時間に応じたログレベル変更
  - 1秒未満: DEBUG
  - 1秒以上: INFO
  - 5秒以上: WARNING
- ✅ エラー発生時のスタックトレース記録

#### 使用例

```python
@performance_monitor
def execute_fit(self, dataset: Dataset, request: FitRequest) -> FitResult:
    # フィッティング処理
    pass

# ログ出力例:
# INFO: ⏱️  app.core.services.fitting.FittingService.execute_fit took 1.23s
# INFO: フィッティング成功: R²=0.9876, RMSE=0.0234
```

---

### 4. 🧱 レイヤードアーキテクチャ

**UI層**（NiceGUI）と**ビジネスロジック層**（Core）を明確に分離しています。

#### メリット
- ✅ UIフレームワークの変更が容易
- ✅ ビジネスロジックの再利用性向上
- ✅ ユニットテストが容易
- ✅ 責務が明確で保守しやすい

```
┌─────────────────────────────────────┐
│  UI Layer (app/ui/)                 │
│  - NiceGUIコンポーネント             │
│  - ページ実装                        │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Service Layer (app/core/services/) │
│  - DatasetService                   │
│  - FittingService                   │
│  - ExportService                    │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Domain Layer (app/core/)           │
│  - Models (Pydantic)                │
│  - Fitting Engine                   │
│  - Utils                            │
└─────────────────────────────────────┘
```

## 使い方

### 1. データのアップロード

1. ホームページから「データアップロード」ページに移動
2. CSVファイルをドラッグ&ドロップ、またはファイル選択
3. データプレビューで内容を確認

**CSVフォーマット:**
```csv
x,y
0.0,1.0
1.0,2.5
2.0,5.2
3.0,10.1
```

### 2. データの可視化

1. X軸・Y軸に使用する列を選択
2. 散布図でデータの傾向を確認
3. 基本統計量を確認

### 3. フィッティングの実行

1. フィッティングモデルを選択
   - 多項式: 次数を1〜10から選択
   - 指数/対数/べき乗: パラメータは自動推定
2. 「フィット実行」ボタンをクリック
3. 結果を確認
   - フィット曲線
   - 残差プロット
   - 統計指標（R², RMSE, AIC, BIC）

### 4. 結果のエクスポート

1. 「結果管理」ページで過去の結果を確認
2. エクスポート形式を選択
   - **JSON**: フィットパラメータと統計情報
   - **CSV**: データポイントと予測値
   - **テキスト**: 人間が読みやすいレポート
3. ダウンロード

---

## 開発

### 開発環境のセットアップ

```bash
# 開発用依存関係を含めてインストール
uv sync --extra dev

# テストの実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=app --cov-report=html

# リンターの実行
uv run ruff check .

# フォーマッター実行
uv run ruff format .

# 型チェック
uv run mypy app/
```

### サンプルデータの生成

```bash
uv run python scripts/make_sample_csv.py
```

複数のパターン（線形、二次、指数など）のサンプルデータが生成されます。

### テスト

```bash
# 全テスト実行
uv run pytest

# 特定のテストファイルのみ
uv run pytest app/tests/test_fitting.py

# 詳細出力
uv run pytest -v

# 失敗時のデバッグ
uv run pytest -vv --pdb
```

**現在のテスト結果:**
- ✅ **11/11 passed** - 全テスト成功
- `TestPolynomialFitter`: 2 tests
- `TestExponentialFitter`: 1 test
- `TestLogarithmicFitter`: 1 test
- `TestPowerFitter`: 1 test
- `TestFitterRegistry`: 6 tests


## 🚀 デプロイ

### ローカル環境

開発・テスト用途：

```bash
uv run python app/main.py
```

### Docker環境

本番相当の環境でテスト：

```bash
docker compose up -d
```

詳細: **[DOCKER_GUIDE.md](./DOCKER_GUIDE.md)**

### AWS EC2

本番環境への公開：

```bash
# EC2接続後
bash <(curl -fsSL https://raw.githubusercontent.com/taka-ttttt/fitCurve/main/deploy/setup_vps.sh)
```

詳細: **[AWS_EC2_DEPLOYMENT.md](./AWS_EC2_DEPLOYMENT.md)**

---

## 📄 ライセンス

MIT License

---

## 👤 作者

**taka-ttttt**

- GitHub: [@taka-ttttt](https://github.com/taka-ttttt)

---

<div align="center">

**Enjoy FitCurve! 🔬📊✨**

</div>