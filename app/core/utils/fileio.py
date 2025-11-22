"""ファイルIO関連ユーティリティ"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def generate_unique_id() -> str:
    """一意なIDを生成
    
    Returns:
        str: UUID4ベースのID
    """
    return str(uuid.uuid4())


def ensure_directory(path: Path | str) -> Path:
    """ディレクトリが存在することを確認、なければ作成
    
    Args:
        path: ディレクトリパス
        
    Returns:
        Path: 作成されたディレクトリパス
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_csv_with_encoding(
    filepath: Path | str,
    encodings: list[str] | None = None
) -> pd.DataFrame:
    """複数のエンコーディングを試してCSVを読み込む
    
    Args:
        filepath: ファイルパス
        encodings: 試すエンコーディングのリスト
        
    Returns:
        pd.DataFrame: 読み込んだデータフレーム
        
    Raises:
        ValueError: すべてのエンコーディングで失敗した場合
    """
    if encodings is None:
        encodings = ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis', 'latin1']
    
    errors = []
    for encoding in encodings:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            if not df.empty:
                return df
        except Exception as e:
            errors.append(f"{encoding}: {str(e)}")
            continue
    
    raise ValueError(
        f"すべてのエンコーディングで読み込みに失敗しました:\n" + "\n".join(errors)
    )


def save_json(data: dict[str, Any], filepath: Path | str) -> None:
    """JSONファイルに保存
    
    Args:
        data: 保存するデータ
        filepath: 保存先パス
    """
    filepath = Path(filepath)
    ensure_directory(filepath.parent)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: Path | str) -> dict[str, Any]:
    """JSONファイルを読み込む
    
    Args:
        filepath: ファイルパス
        
    Returns:
        dict: 読み込んだデータ
    """
    filepath = Path(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_files_by_pattern(
    directory: Path | str,
    pattern: str = "*",
    sort_by_mtime: bool = True
) -> list[Path]:
    """パターンマッチでファイルをリスト
    
    Args:
        directory: 検索ディレクトリ
        pattern: グロブパターン
        sort_by_mtime: 更新日時でソートするか
        
    Returns:
        list[Path]: ファイルパスのリスト
    """
    directory = Path(directory)
    if not directory.exists():
        return []
    
    files = list(directory.glob(pattern))
    
    if sort_by_mtime:
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    return files


def get_file_info(filepath: Path | str) -> dict[str, Any]:
    """ファイル情報を取得
    
    Args:
        filepath: ファイルパス
        
    Returns:
        dict: ファイル情報
    """
    filepath = Path(filepath)
    stat = filepath.stat()
    
    return {
        "name": filepath.name,
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime),
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "extension": filepath.suffix
    }


def sanitize_filename(filename: str) -> str:
    """ファイル名をサニタイズ
    
    Args:
        filename: 元のファイル名
        
    Returns:
        str: サニタイズされたファイル名
    """
    # 危険な文字を除去
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # 長すぎる場合は切り詰め
    max_length = 200
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name
    
    return filename

