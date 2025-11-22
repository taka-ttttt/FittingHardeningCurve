"""Ludwik硬化則モデル"""

import numpy as np
from scipy.optimize import curve_fit
from typing import Any

from app.core.fitting.base import BaseFitter
from app.core.models.fit_request import FitConfig


class LudwikFitter(BaseFitter):
    """Ludwik硬化則フィッター
    
    σ = σ₀ + K * ε^n
    """
    
    def __init__(self, config: FitConfig | None = None):
        if config is None:
            config = FitConfig(method="ludwik")
        super().__init__(config)
        self.name = "Ludwik硬化則"
        self.description = "σ = σ₀ + K * ε^n"
        self.param_names = ["σ₀", "K", "n"]
        # bounds: ([下限...], [上限...])
        self.param_bounds = (
            [0, 0, 0],           # 下限: σ₀, K, n
            [np.inf, np.inf, 2]  # 上限: σ₀, K, n
        )
    
    def model_function(self, strain: np.ndarray, sigma_0: float, K: float, n: float) -> np.ndarray:
        """Ludwik硬化則モデル関数
        
        Args:
            strain: ひずみ配列
            sigma_0: 初期応力 (MPa)
            K: 硬化係数 (MPa)
            n: 硬化指数
            
        Returns:
            応力配列
        """
        return sigma_0 + K * np.power(strain, n)
    
    def fit(self, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """フィッティング実行
        
        Args:
            x: ひずみデータ
            y: 応力データ
            
        Returns:
            dict: フィット結果
        """
        # 初期値の推定
        # σ₀: ひずみ=0に最も近い点の応力値を使用（固定値）
        min_strain_idx = np.argmin(np.abs(x))
        sigma_0_fixed = float(y[min_strain_idx])
        
        # σ₀を固定したモデル関数
        def model_with_fixed_sigma0(strain, K, n):
            return self.model_function(strain, sigma_0_fixed, K, n)
        
        K_init = (np.max(y) - sigma_0_fixed) / np.power(np.max(x), 0.5) if np.max(x) > 0 else 1.0
        n_init = 0.5  # 硬化指数の初期値
        
        initial_guess = [K_init, n_init]
        
        # パラメータ制約を設定（σ₀は除外）
        bounds = ([0, 0], [np.inf, 2])
        if self.config.param_bounds:
            # カスタム制約が指定されている場合
            custom_bounds = self.config.param_bounds
            lower_bounds = [
                custom_bounds.get('K', (0, np.inf))[0],
                custom_bounds.get('n', (0, 2))[0]
            ]
            upper_bounds = [
                custom_bounds.get('K', (0, np.inf))[1],
                custom_bounds.get('n', (0, 2))[1]
            ]
            bounds = (lower_bounds, upper_bounds)
        
        try:
            popt, pcov = curve_fit(
                model_with_fixed_sigma0,
                x,
                y,
                p0=initial_guess,
                bounds=bounds,
                maxfev=10000
            )
            
            # パラメータ辞書を作成
            parameters = {
                self.param_names[0]: sigma_0_fixed,  # σ₀ (固定値)
                self.param_names[1]: float(popt[0]),  # K
                self.param_names[2]: float(popt[1]),  # n
            }
            
            return {
                "parameters": parameters,
                "covariance": pcov,
                "success": True,
                "message": "Ludwik硬化則フィッティングが成功しました"
            }
        except Exception as e:
            import traceback
            error_msg = f"Ludwik硬化則フィッティングエラー: {str(e)}\n{traceback.format_exc()}"
            return {
                "parameters": {},
                "covariance": None,
                "success": False,
                "message": error_msg
            }
    
    def predict(self, x: np.ndarray, parameters: dict[str, float]) -> np.ndarray:
        """予測値を計算
        
        Args:
            x: X値の配列
            parameters: フィットパラメータ
            
        Returns:
            np.ndarray: 予測Y値
        """
        sigma_0 = parameters[self.param_names[0]]
        K = parameters[self.param_names[1]]
        n = parameters[self.param_names[2]]
        
        return self.model_function(x, sigma_0, K, n)
    
    def get_parameter_info(self) -> list[dict]:
        """パラメータ情報を取得"""
        return [
            {
                "name": "σ₀",
                "description": "初期応力 (MPa)",
                "unit": "MPa",
                "typical_range": "0-500"
            },
            {
                "name": "K",
                "description": "硬化係数 (MPa)",
                "unit": "MPa",
                "typical_range": "100-2000"
            },
            {
                "name": "n",
                "description": "硬化指数",
                "unit": "-",
                "typical_range": "0.1-1.0"
            }
        ]
