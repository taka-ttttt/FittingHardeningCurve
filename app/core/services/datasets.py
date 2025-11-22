"""データセット管理サービス"""

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from nicegui import app

from app.core.models.dataset import Dataset, DatasetMetadata
from app.core.utils.fileio import (
    ensure_directory,
    generate_unique_id,
    read_csv_with_encoding,
    sanitize_filename,
)


class DatasetService:
    """データセット管理サービス"""
    
    def __init__(self, upload_dir: Path | str = "data/uploads"):
        """初期化
        
        Args:
            upload_dir: アップロードファイルの保存先
        """
        self.upload_dir = Path(upload_dir)
        ensure_directory(self.upload_dir)
        
        # ストレージの初期化
        if 'datasets' not in app.storage.general:
            app.storage.general['datasets'] = {}
        if 'current_dataset_id' not in app.storage.general:
            app.storage.general['current_dataset_id'] = None
    
    async def load_from_upload(
        self,
        file_content: bytes,
        filename: str,
        encodings: list[str] | None = None
    ) -> Dataset:
        """アップロードファイルからデータセットを作成
        
        Args:
            file_content: ファイル内容（バイト）
            filename: ファイル名
            encodings: 試すエンコーディングのリスト
            
        Returns:
            Dataset: 作成されたデータセット
            
        Raises:
            ValueError: データ読み込みに失敗した場合
        """
        if encodings is None:
            encodings = ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis']
        
        # エンコーディングを試行
        df = None
        errors = []
        
        for encoding in encodings:
            try:
                df = pd.read_csv(BytesIO(file_content), encoding=encoding)
                if not df.empty:
                    break
            except Exception as e:
                errors.append(f"{encoding}: {str(e)}")
                continue
        
        if df is None or df.empty:
            raise ValueError(
                f"CSVの読み込みに失敗しました:\n" + "\n".join(errors)
            )
        
        # カンマや全角スペースを除去して数値化を試みる
        df = self._clean_numeric_columns(df)
        
        # データセットを作成
        dataset_id = generate_unique_id()
        safe_filename = sanitize_filename(filename)
        filepath = self.upload_dir / f"{dataset_id}_{safe_filename}"
        
        # ファイルを保存
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        dataset = Dataset(
            id=dataset_id,
            filename=filename,
            filepath=filepath,
            data=df
        )
        
        return dataset
    
    def load_from_file(
        self,
        filepath: Path | str,
        encodings: list[str] | None = None
    ) -> Dataset:
        """ファイルパスからデータセットを作成
        
        Args:
            filepath: ファイルパス
            encodings: 試すエンコーディングのリスト
            
        Returns:
            Dataset: 作成されたデータセット
        """
        filepath = Path(filepath)
        
        df = read_csv_with_encoding(filepath, encodings)
        df = self._clean_numeric_columns(df)
        
        dataset = Dataset(
            id=generate_unique_id(),
            filename=filepath.name,
            filepath=filepath,
            data=df
        )
        
        return dataset
    
    def validate_dataset(self, dataset: Dataset) -> dict[str, Any]:
        """データセットの妥当性をチェック
        
        Args:
            dataset: チェックするデータセット
            
        Returns:
            dict: バリデーション結果
                - valid: bool
                - errors: list[str]
                - warnings: list[str]
        """
        errors = []
        warnings = []
        
        # 行数チェック
        if len(dataset.data) < 3:
            errors.append("データが3行未満です。フィッティングには最低3点必要です。")
        
        # 列数チェック
        if dataset.data.shape[1] < 2:
            errors.append("データが2列未満です。X軸とY軸に最低2列必要です。")
        
        # 数値列のチェック
        numeric_cols = dataset.data.select_dtypes(include=['number']).columns
        if len(numeric_cols) < 2:
            errors.append("数値列が2列未満です。")
        
        # 欠損値チェック
        if dataset.data.isnull().any().any():
            null_counts = dataset.data.isnull().sum()
            null_cols = null_counts[null_counts > 0]
            warnings.append(
                f"欠損値が含まれています: {dict(null_cols)}"
            )
        
        # 重複行チェック
        n_duplicates = dataset.data.duplicated().sum()
        if n_duplicates > 0:
            warnings.append(f"重複行が{n_duplicates}行あります。")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_column_info(self, dataset: Dataset) -> list[dict[str, Any]]:
        """各列の情報を取得
        
        Args:
            dataset: データセット
            
        Returns:
            list: 列情報のリスト
        """
        info = []
        
        for col in dataset.data.columns:
            col_data = dataset.data[col]
            
            col_info = {
                "name": col,
                "dtype": str(col_data.dtype),
                "null_count": int(col_data.isnull().sum()),
                "unique_count": int(col_data.nunique()),
            }
            
            # 数値列の場合は統計情報を追加
            if pd.api.types.is_numeric_dtype(col_data):
                col_info.update({
                    "min": float(col_data.min()),
                    "max": float(col_data.max()),
                    "mean": float(col_data.mean()),
                    "std": float(col_data.std()),
                    "is_numeric": True
                })
            else:
                col_info["is_numeric"] = False
            
            info.append(col_info)
        
        return info
    
    def _clean_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """数値列をクリーニング
        
        Args:
            df: データフレーム
            
        Returns:
            pd.DataFrame: クリーニング後のデータフレーム
        """
        for col in df.columns:
            # 文字列型の場合のみクリーニング
            if df[col].dtype == object:
                # カンマ、全角スペースを除去
                cleaned = df[col].astype(str).str.replace(',', '', regex=False)
                cleaned = cleaned.str.replace('\u3000', ' ', regex=False)
                cleaned = cleaned.str.strip()
                
                # 数値変換を試みる
                try:
                    df[col] = pd.to_numeric(cleaned, errors='coerce')
                except Exception:
                    pass  # 変換失敗の場合は元のまま
        
        return df
    
    def save_dataset(self, dataset: Dataset) -> None:
        """データセットをストレージに保存
        
        Args:
            dataset: 保存するデータセット
        """
        # データセットをシリアライズして保存
        app.storage.general['datasets'][dataset.id] = dataset.model_dump()
    
    def get_dataset(self, dataset_id: str) -> Dataset | None:
        """IDでデータセットを取得
        
        Args:
            dataset_id: データセットID
            
        Returns:
            Dataset | None: データセット（存在しない場合はNone）
        """
        if dataset_id not in app.storage.general.get('datasets', {}):
            return None
        
        dataset_dict = app.storage.general['datasets'][dataset_id]
        return Dataset.model_validate(dataset_dict)
    
    def get_current_dataset(self) -> Dataset | None:
        """現在のデータセットを取得
        
        Returns:
            Dataset | None: 現在のデータセット（存在しない場合はNone）
        """
        current_id = app.storage.general.get('current_dataset_id')
        if current_id is None:
            return None
        
        return self.get_dataset(current_id)
    
    def set_current_dataset(self, dataset: Dataset) -> None:
        """現在のデータセットを設定
        
        Args:
            dataset: 設定するデータセット
        """
        # データセットを保存
        self.save_dataset(dataset)
        # 現在のIDを更新
        app.storage.general['current_dataset_id'] = dataset.id
    
    def get_all_datasets(self) -> list[Dataset]:
        """すべてのデータセットを取得
        
        Returns:
            list[Dataset]: データセットのリスト
        """
        datasets = []
        for dataset_dict in app.storage.general.get('datasets', {}).values():
            try:
                datasets.append(Dataset.model_validate(dataset_dict))
            except Exception:
                continue
        
        return sorted(datasets, key=lambda d: d.uploaded_at, reverse=True)
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """データセットを削除
        
        Args:
            dataset_id: データセットID
            
        Returns:
            bool: 削除成功したかどうか
        """
        if dataset_id not in app.storage.general.get('datasets', {}):
            return False
        
        # ストレージから削除
        del app.storage.general['datasets'][dataset_id]
        
        # 現在のデータセットだった場合はクリア
        if app.storage.general.get('current_dataset_id') == dataset_id:
            app.storage.general['current_dataset_id'] = None
        
        return True

