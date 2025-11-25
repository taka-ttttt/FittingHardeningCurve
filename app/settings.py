"""アプリケーション設定"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # アプリケーション基本設定
    app_env: Literal["development", "production"] = "development"
    app_debug: bool = True
    app_host: str = "127.0.0.1"  # 本番環境では "0.0.0.0" を推奨
    app_port: int = 5173
    
    # ディレクトリ設定
    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    fits_dir: Path = Path("data/fits")
    cache_dir: Path = Path("data/cache")
    
    # ファイルサイズ制限（MB）
    max_upload_size: int = 10
    
    # ログ設定
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_file: Path | None = None
    
    # デフォルトフィッティング設定
    default_fit_method: Literal["poly", "exp", "log", "power"] = "poly"
    default_poly_degree: int = 3
    
    @property
    def debug(self) -> bool:
        """デバッグモード"""
        return self.app_debug or self.app_env == "development"
    
    def ensure_directories(self) -> None:
        """必要なディレクトリを作成"""
        for dir_path in [self.data_dir, self.upload_dir, self.fits_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


# グローバル設定インスタンス
settings = Settings()
settings.ensure_directories()

