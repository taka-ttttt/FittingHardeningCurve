"""Voce硬化則モデル"""

import numpy as np
from scipy.optimize import curve_fit
from typing import Any

from app.core.fitting.base import BaseFitter
from app.core.models.fit_request import FitConfig


class VoceFitter(BaseFitter):
    """Voce硬化則フィッター
    
    σ = σ₀ + (σ∞ - σ₀) * (1 - exp(-C * ε))
    """
    
    def __init__(self, config: FitConfig | None = None):
        if config is None:
            config = FitConfig(method="voce")
        super().__init__(config)
        self.name = "Voce硬化則"
        self.description = "σ = σ₀ + (σ∞ - σ₀) * (1 - exp(-C * ε))"
        self.param_names = ["σ₀", "σ∞", "C"]
        # bounds: ([下限...], [上限...])
        self.param_bounds = (
            [0, 0, 0],                    # 下限: σ₀, σ∞, C
            [np.inf, np.inf, np.inf]      # 上限: σ₀, σ∞, C
        )
    
    def model_function(self, strain: np.ndarray, sigma_0: float, sigma_inf: float, C: float) -> np.ndarray:
        """Voce硬化則モデル関数
        
        Args:
            strain: ひずみ配列
            sigma_0: 初期応力 (MPa)
            sigma_inf: 飽和応力 (MPa)
            C: 硬化係数
            
        Returns:
            応力配列
        """
        return sigma_0 + (sigma_inf - sigma_0) * (1 - np.exp(-C * strain))
    
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
        def model_with_fixed_sigma0(strain, sigma_inf, C):
            return self.model_function(strain, sigma_0_fixed, sigma_inf, C)
        
        sigma_inf_init = np.max(y)  # 最大応力を飽和応力として推定
        C_init = 10.0  # 硬化係数の初期値
        
        initial_guess = [sigma_inf_init, C_init]
        
        # パラメータ制約を設定（σ₀は除外）
        bounds = ([0, 0], [np.inf, np.inf])
        if self.config.param_bounds:
            # カスタム制約が指定されている場合
            custom_bounds = self.config.param_bounds
            lower_bounds = [
                custom_bounds.get('σ∞', (0, np.inf))[0],
                custom_bounds.get('C', (0, np.inf))[0]
            ]
            upper_bounds = [
                custom_bounds.get('σ∞', (0, np.inf))[1],
                custom_bounds.get('C', (0, np.inf))[1]
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
                self.param_names[1]: float(popt[0]),  # σ∞
                self.param_names[2]: float(popt[1]),  # C
            }
            
            return {
                "parameters": parameters,
                "covariance": pcov,
                "success": True,
                "message": "Voce硬化則フィッティングが成功しました"
            }
        except Exception as e:
            return {
                "parameters": {},
                "covariance": None,
                "success": False,
                "message": f"Voce硬化則フィッティングエラー: {str(e)}"
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
        sigma_inf = parameters[self.param_names[1]]
        C = parameters[self.param_names[2]]
        
        return self.model_function(x, sigma_0, sigma_inf, C)
    
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
                "name": "σ∞",
                "description": "飽和応力 (MPa)",
                "unit": "MPa",
                "typical_range": "200-2000"
            },
            {
                "name": "C",
                "description": "硬化係数",
                "unit": "-",
                "typical_range": "1-100"
            }
        ]
