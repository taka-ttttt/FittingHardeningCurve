"""前処理サービス"""

import numpy as np
import pandas as pd
from pathlib import Path

from app.core.models.dataset import Dataset


class PreprocessingService:
    """前処理サービス"""
    
    @staticmethod
    def convert_strain_percent_to_dimensionless(strain: np.ndarray) -> np.ndarray:
        """ひずみを%から無次元に変換
        
        Args:
            strain: ひずみ（%）
            
        Returns:
            np.ndarray: 無次元ひずみ
        """
        return strain / 100.0
    
    @staticmethod
    def convert_nominal_to_true_strain(nominal_strain: np.ndarray) -> np.ndarray:
        """公称ひずみを真ひずみに変換
        
        Args:
            nominal_strain: 公称ひずみ
            
        Returns:
            np.ndarray: 真ひずみ
            
        Formula:
            ε_true = ln(1 + ε_nominal)
        """
        return np.log(1 + nominal_strain)
    
    @staticmethod
    def convert_nominal_to_true_stress(
        nominal_stress: np.ndarray,
        nominal_strain: np.ndarray
    ) -> np.ndarray:
        """公称応力を真応力に変換
        
        Args:
            nominal_stress: 公称応力
            nominal_strain: 公称ひずみ
            
        Returns:
            np.ndarray: 真応力
            
        Formula:
            σ_true = σ_nominal * (1 + ε_nominal)
        """
        return nominal_stress * (1 + nominal_strain)
    
    @staticmethod
    def convert_total_to_plastic_strain(
        total_strain: np.ndarray,
        stress: np.ndarray,
        youngs_modulus: float,
        yield_stress: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """全ひずみを塑性ひずみに変換
        
        Args:
            total_strain: 全ひずみ
            stress: 応力
            youngs_modulus: ヤング率 (E)
            yield_stress: 降伏応力 (σ_y)
            
        Returns:
            tuple[np.ndarray, np.ndarray]: (塑性ひずみ, 応力) - 降伏点以降のみ
            
        Formula:
            ε_plastic = ε_total - σ / E
            降伏応力以上のデータのみを返す
        """
        # 弾性ひずみを計算
        elastic_strain = stress / youngs_modulus
        
        # 塑性ひずみを計算
        plastic_strain = total_strain - elastic_strain
        
        # 降伏応力以上のデータのみをフィルタリング
        mask = stress >= yield_stress
        
        return plastic_strain[mask], stress[mask]
    
    @staticmethod
    def apply_preprocessing(
        dataset: Dataset,
        x_column: str,
        y_column: str,
        strain_unit_percent: bool = False,
        convert_to_true: bool = False,
        convert_to_plastic: bool = False,
        youngs_modulus: float | None = None,
        yield_stress: float | None = None
    ) -> Dataset:
        """前処理を適用
        
        Args:
            dataset: 元のデータセット
            x_column: X軸の列名
            y_column: Y軸の列名
            strain_unit_percent: ひずみが%単位の場合True
            convert_to_true: 公称→真への変換を行う場合True
            convert_to_plastic: 全→塑性への変換を行う場合True
            youngs_modulus: ヤング率（塑性変換時に必要）
            yield_stress: 降伏応力（塑性変換時に必要）
            
        Returns:
            Dataset: 前処理後のデータセット
        """
        # データを取得
        x_data, y_data = dataset.get_xy_data(x_column, y_column, dropna=True)
        
        # 1. ひずみ単位変換（%→無次元）
        if strain_unit_percent:
            x_data = PreprocessingService.convert_strain_percent_to_dimensionless(x_data)
        
        # 2. 公称→真への変換
        if convert_to_true:
            # 注意: 真応力の計算には公称ひずみを使う
            y_data = PreprocessingService.convert_nominal_to_true_stress(y_data, x_data)
            x_data = PreprocessingService.convert_nominal_to_true_strain(x_data)
        
        # 3. 全ひずみ→塑性ひずみへの変換
        if convert_to_plastic:
            if youngs_modulus is None or yield_stress is None:
                raise ValueError("塑性ひずみ変換にはヤング率と降伏応力が必要です")
            
            x_data, y_data = PreprocessingService.convert_total_to_plastic_strain(
                x_data, y_data, youngs_modulus, yield_stress
            )
        
        # 新しいデータフレームを作成
        new_df = pd.DataFrame({
            x_column: x_data,
            y_column: y_data
        })
        
        # 新しいファイルパスを作成（元のファイルパスに_preprocessedを追加）
        new_filepath = dataset.filepath.parent / f"{dataset.filepath.stem}_preprocessed{dataset.filepath.suffix}"
        
        # 新しいデータセットを作成
        new_dataset = Dataset(
            id=dataset.id,
            filename=f"{dataset.filename}_preprocessed",
            filepath=new_filepath,
            data=new_df,
            uploaded_at=dataset.uploaded_at
        )
        
        return new_dataset

