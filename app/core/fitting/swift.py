"""Swift硬化則モデル"""

import numpy as np
from scipy.optimize import curve_fit
from typing import Any

from app.core.fitting.base import BaseFitter
from app.core.models.fit_request import FitConfig


class SwiftFitter(BaseFitter):
    """Swift硬化則フィッター
    
    σ = K * (ε₀ + ε)^n
    """
    
    def __init__(self, config: FitConfig | None = None):
        if config is None:
            config = FitConfig(method="swift")
        super().__init__(config)
        self.name = "Swift硬化則"
        self.description = "σ = K * (ε₀ + ε)^n"
        self.param_names = ["K", "ε₀", "n"]
        # bounds: ([下限...], [上限...])
        self.param_bounds = (
            [0, 0, 0],              # 下限: K, ε₀, n
            [np.inf, 0.1, 2]        # 上限: K, ε₀, n
        )
    
    def model_function(self, strain: np.ndarray, K: float, epsilon_0: float, n: float) -> np.ndarray:
        """Swift硬化則モデル関数
        
        Args:
            strain: ひずみ配列
            K: 硬化係数 (MPa)
            epsilon_0: 初期ひずみ
            n: 硬化指数
            
        Returns:
            応力配列
        """
        return K * np.power(epsilon_0 + strain, n)
    
    def fit(self, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """フィッティング実行
        
        Args:
            x: ひずみデータ
            y: 応力データ
            
        Returns:
            dict: フィット結果
        """
        # 初期値の推定
        K_init = np.max(y) / np.power(np.max(x), 0.5) if np.max(x) > 0 else 1.0
        epsilon_0_init = 0.01  # 初期ひずみの初期値
        n_init = 0.5  # 硬化指数の初期値
        
        initial_guess = [K_init, epsilon_0_init, n_init]
        
        # パラメータ制約を設定
        bounds = self.param_bounds
        if self.config.param_bounds:
            # カスタム制約が指定されている場合
            custom_bounds = self.config.param_bounds
            lower_bounds = [
                custom_bounds.get('K', (0, np.inf))[0],
                custom_bounds.get('ε₀', (0, 0.1))[0],
                custom_bounds.get('n', (0, 2))[0]
            ]
            upper_bounds = [
                custom_bounds.get('K', (0, np.inf))[1],
                custom_bounds.get('ε₀', (0, 0.1))[1],
                custom_bounds.get('n', (0, 2))[1]
            ]
            bounds = (lower_bounds, upper_bounds)
        
        try:
            popt, pcov = curve_fit(
                self.model_function,
                x,
                y,
                p0=initial_guess,
                bounds=bounds,
                maxfev=10000
            )
            
            # パラメータ辞書を作成
            parameters = {
                self.param_names[0]: float(popt[0]),  # K
                self.param_names[1]: float(popt[1]),  # ε₀
                self.param_names[2]: float(popt[2]),  # n
            }
            
            return {
                "parameters": parameters,
                "covariance": pcov,
                "success": True,
                "message": "Swift硬化則フィッティングが成功しました"
            }
        except Exception as e:
            return {
                "parameters": {},
                "covariance": None,
                "success": False,
                "message": f"Swift硬化則フィッティングエラー: {str(e)}"
            }
    
    def predict(self, x: np.ndarray, parameters: dict[str, float]) -> np.ndarray:
        """予測値を計算
        
        Args:
            x: X値の配列
            parameters: フィットパラメータ
            
        Returns:
            np.ndarray: 予測Y値
        """
        K = parameters[self.param_names[0]]
        epsilon_0 = parameters[self.param_names[1]]
        n = parameters[self.param_names[2]]
        
        return self.model_function(x, K, epsilon_0, n)
    
    def get_parameter_info(self) -> list[dict]:
        """パラメータ情報を取得"""
        return [
            {
                "name": "K",
                "description": "硬化係数 (MPa)",
                "unit": "MPa",
                "typical_range": "100-2000"
            },
            {
                "name": "ε₀",
                "description": "初期ひずみ",
                "unit": "-",
                "typical_range": "0.001-0.1"
            },
            {
                "name": "n",
                "description": "硬化指数",
                "unit": "-",
                "typical_range": "0.1-1.0"
            }
        ]
