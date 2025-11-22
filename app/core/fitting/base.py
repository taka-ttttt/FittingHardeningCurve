"""フィッティングの基底クラス"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from app.core.models.fit_request import FitConfig
from app.core.models.fit_result import FitResult, FitStatistics


class BaseFitter(ABC):
    """フィッター基底クラス"""
    
    def __init__(self, config: FitConfig):
        """初期化
        
        Args:
            config: フィッティング設定
        """
        self.config = config
    
    @abstractmethod
    def fit(self, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """フィッティングを実行
        
        Args:
            x: X値の配列
            y: Y値の配列
            
        Returns:
            dict: フィット結果
                - parameters: パラメータ辞書
                - covariance: 共分散行列
                - success: 成功フラグ
                - message: メッセージ
        """
        pass
    
    @abstractmethod
    def predict(self, x: np.ndarray, parameters: dict[str, float]) -> np.ndarray:
        """予測値を計算
        
        Args:
            x: X値の配列
            parameters: フィットパラメータ
            
        Returns:
            np.ndarray: 予測Y値
        """
        pass
    
    def calculate_residuals(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> np.ndarray:
        """残差を計算
        
        Args:
            y_true: 実測値
            y_pred: 予測値
            
        Returns:
            np.ndarray: 残差
        """
        return y_true - y_pred
    
    def calculate_statistics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        n_params: int
    ) -> FitStatistics:
        """統計指標を計算
        
        Args:
            y_true: 実測値
            y_pred: 予測値
            n_params: パラメータ数
            
        Returns:
            FitStatistics: 統計情報
        """
        n = len(y_true)
        residuals = self.calculate_residuals(y_true, y_pred)
        
        # 残差平方和 (RSS)
        rss = np.sum(residuals**2)
        
        # 全平方和 (TSS)
        y_mean = np.mean(y_true)
        tss = np.sum((y_true - y_mean)**2)
        
        # R²（決定係数）
        r_squared = 1 - (rss / tss) if tss > 0 else 0.0
        
        # 調整済みR²
        if n > n_params:
            adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - n_params - 1)
        else:
            adjusted_r_squared = r_squared
        
        # RMSE（二乗平均平方根誤差）
        rmse = np.sqrt(rss / n)
        
        # MAE（平均絶対誤差）
        mae = np.mean(np.abs(residuals))
        
        # 最大誤差
        max_error = np.max(np.abs(residuals))
        
        # AIC（赤池情報量規準）
        if rss > 0:
            aic = n * np.log(rss / n) + 2 * n_params
        else:
            aic = float('-inf')
        
        # BIC（ベイズ情報量規準）
        if rss > 0:
            bic = n * np.log(rss / n) + n_params * np.log(n)
        else:
            bic = float('-inf')
        
        return FitStatistics(
            r_squared=float(r_squared),
            adjusted_r_squared=float(adjusted_r_squared),
            rmse=float(rmse),
            mae=float(mae),
            max_error=float(max_error),
            aic=float(aic),
            bic=float(bic),
            residual_sum_squares=float(rss),
            total_sum_squares=float(tss)
        )
    
    def calculate_parameter_errors(
        self,
        covariance: np.ndarray | None,
        param_names: list[str]
    ) -> dict[str, float] | None:
        """パラメータの標準誤差を計算
        
        Args:
            covariance: 共分散行列
            param_names: パラメータ名のリスト
            
        Returns:
            dict | None: パラメータ誤差の辞書
        """
        if covariance is None:
            return None
        
        # 対角成分の平方根が標準誤差
        errors = np.sqrt(np.diag(covariance))
        return {name: float(err) for name, err in zip(param_names, errors)}
    
    def execute(
        self,
        x: np.ndarray,
        y: np.ndarray,
        result_id: str,
        dataset_id: str,
        name: str | None = None,
        description: str | None = None
    ) -> FitResult:
        """フィッティングを実行してFitResultを返す
        
        Args:
            x: X値
            y: Y値
            result_id: 結果ID
            dataset_id: データセットID
            name: 結果名
            description: 結果説明
            
        Returns:
            FitResult: フィット結果
        """
        # データ範囲でフィルタリング
        if self.config.x_range is not None:
            x_min, x_max = self.config.x_range
            mask = (x >= x_min) & (x <= x_max)
            x = x[mask]
            y = y[mask]
        
        # フィッティング実行
        fit_result = self.fit(x, y)
        
        # デバッグ用ログ
        print(f"DEBUG: fit_result = {fit_result}")
        print(f"DEBUG: fit_result type = {type(fit_result)}")
        
        if not fit_result["success"]:
            # フィット失敗
            return FitResult(
                id=result_id,
                name=name,
                description=description,
                dataset_id=dataset_id,
                config=self.config,
                parameters={},
                statistics=FitStatistics(
                    r_squared=0, adjusted_r_squared=0, rmse=0, mae=0,
                    max_error=0, aic=0, bic=0, residual_sum_squares=0,
                    total_sum_squares=0
                ),
                x_data=x,
                y_data=y,
                y_fitted=np.zeros_like(y),
                residuals=np.zeros_like(y),
                success=False,
                message=fit_result.get("message", "フィットに失敗しました")
            )
        
        # 予測値を計算
        parameters = fit_result["parameters"]
        y_fitted = self.predict(x, parameters)
        
        # 残差を計算
        residuals = self.calculate_residuals(y, y_fitted)
        
        # 統計情報を計算
        n_params = len(parameters)
        statistics = self.calculate_statistics(y, y_fitted, n_params)
        
        # パラメータエラーを計算
        param_names = list(parameters.keys())
        parameter_errors = self.calculate_parameter_errors(
            fit_result.get("covariance"),
            param_names
        )
        
        return FitResult(
            id=result_id,
            name=name,
            description=description,
            dataset_id=dataset_id,
            config=self.config,
            parameters=parameters,
            parameter_errors=parameter_errors,
            covariance_matrix=fit_result.get("covariance"),
            statistics=statistics,
            x_data=x,
            y_data=y,
            y_fitted=y_fitted,
            residuals=residuals,
            success=True,
            message=fit_result.get("message")
        )

