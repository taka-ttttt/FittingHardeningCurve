"""データセット関連のモデル"""

from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator


class DatasetMetadata(BaseModel):
    """データセットのメタ情報"""
    
    n_rows: int = Field(description="行数")
    n_cols: int = Field(description="列数")
    column_names: list[str] = Field(description="列名リスト")
    x_column: str = Field(description="X軸に使用する列名")
    y_column: str = Field(description="Y軸に使用する列名")
    x_min: float = Field(description="X軸の最小値")
    x_max: float = Field(description="X軸の最大値")
    y_min: float = Field(description="Y軸の最小値")
    y_max: float = Field(description="Y軸の最大値")
    x_mean: float = Field(description="X軸の平均値")
    y_mean: float = Field(description="Y軸の平均値")
    x_std: float = Field(description="X軸の標準偏差")
    y_std: float = Field(description="Y軸の標準偏差")


class Dataset(BaseModel):
    """アップロードされたデータセット"""
    
    model_config = {"arbitrary_types_allowed": True}
    
    id: str = Field(description="データセットID")
    filename: str = Field(description="ファイル名")
    filepath: Path = Field(description="ファイルパス")
    uploaded_at: datetime = Field(default_factory=datetime.now)
    parent_id: str | None = Field(default=None, description="親データセットID")
    tags: list[str] = Field(default_factory=list, description="タグ")
    data: pd.DataFrame = Field(description="データフレーム")
    metadata: DatasetMetadata | None = Field(default=None, description="メタ情報")
    
    @field_validator("data")
    @classmethod
    def validate_data(cls, v: pd.DataFrame) -> pd.DataFrame:
        """データフレームのバリデーション"""
        if v.empty:
            raise ValueError("データが空です")
        if v.shape[1] < 2:
            raise ValueError("最低2列必要です")
        return v
    
    def get_xy_data(
        self, 
        x_col: str | None = None, 
        y_col: str | None = None,
        dropna: bool = True
    ) -> tuple[np.ndarray, np.ndarray]:
        """X, Yデータを取得
        
        Args:
            x_col: X列名（指定しない場合は最初の列）
            y_col: Y列名（指定しない場合は2番目の列）
            dropna: NaN値を除去するか
            
        Returns:
            (x_array, y_array): NumPy配列のタプル
        """
        x_name = x_col or self.data.columns[0]
        y_name = y_col or self.data.columns[1]
        
        x = pd.to_numeric(self.data[x_name], errors='coerce')
        y = pd.to_numeric(self.data[y_name], errors='coerce')
        
        if dropna:
            mask = x.notna() & y.notna()
            x = x[mask]
            y = y[mask]
        
        return x.values, y.values
    
    def calculate_metadata(
        self,
        x_col: str | None = None,
        y_col: str | None = None
    ) -> DatasetMetadata:
        """メタ情報を計算
        
        Args:
            x_col: X列名
            y_col: Y列名
            
        Returns:
            DatasetMetadata: 計算されたメタ情報
        """
        x, y = self.get_xy_data(x_col, y_col, dropna=True)
        
        x_name = x_col or self.data.columns[0]
        y_name = y_col or self.data.columns[1]
        
        metadata = DatasetMetadata(
            n_rows=len(x),
            n_cols=self.data.shape[1],
            column_names=self.data.columns.tolist(),
            x_column=x_name,
            y_column=y_name,
            x_min=float(np.min(x)),
            x_max=float(np.max(x)),
            y_min=float(np.min(y)),
            y_max=float(np.max(y)),
            x_mean=float(np.mean(x)),
            y_mean=float(np.mean(y)),
            x_std=float(np.std(x)),
            y_std=float(np.std(y))
        )
        
        self.metadata = metadata
        return metadata

