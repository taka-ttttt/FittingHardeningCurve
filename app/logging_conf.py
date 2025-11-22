"""ログ設定"""

import logging
import sys
from pathlib import Path

from app.settings import settings


def setup_logging() -> None:
    """ログ設定を初期化"""
    
    # ログフォーマット
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # ロガー設定
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level))
    
    # 既存のハンドラをクリア
    logger.handlers.clear()
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)
    
    # ファイルハンドラ（設定されている場合）
    if settings.log_file:
        log_file = Path(settings.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """名前付きロガーを取得
    
    Args:
        name: ロガー名
        
    Returns:
        logging.Logger: ロガー
    """
    return logging.getLogger(name)

