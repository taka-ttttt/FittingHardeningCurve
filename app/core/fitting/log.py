"""対数関数フィッティング"""

from typing import Any

import numpy as np
from scipy.optimize import curve_fit

from app.core.fitting.base import BaseFitter
from app.core.models.fit_request import FitConfig


class LogarithmicFitter(BaseFitter):
    """対数関数フィッター
    
    モデル: y = a + b * ln(x)
    """
    
    def fit(self, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """対数関数フィッティングを実行
        
        Args:
            x: X値の配列
            y: Y値の配列
            
        Returns:
            dict: フィット結果
        """
        # x > 0 のチェック
        if np.any(x <= 0):
            return {
                "parameters": {},
                "covariance": None,
                "success": False,
                "message": "対数フィットにはx > 0が必要です"
            }
        
        def log_func(x: np.ndarray, a: float, b: float) -> np.ndarray:
            """対数関数"""
            return a + b * np.log(x)
        
        try:
            # 初期値
            if self.config.initial_params:
                p0 = [
                    self.config.initial_params.get("a", 0.0),
                    self.config.initial_params.get("b", 1.0)
                ]
            else:
                # 線形回帰で初期値推定: y = a + b * ln(x)
                log_x = np.log(x)
                coeffs = np.polyfit(log_x, y, 1)
                p0 = [coeffs[1], coeffs[0]]  # [切片, 傾き]
            
            # 重み付け
            sigma = None
            if self.config.use_weights and self.config.weights is not None:
                sigma = 1.0 / np.array(self.config.weights)
            
            # curve_fitで最適化
            popt, pcov = curve_fit(
                log_func, x, y,
                p0=p0,
                sigma=sigma,
                absolute_sigma=True,
                maxfev=self.config.max_iterations
            )
            
            parameters = {
                "a": float(popt[0]),
                "b": float(popt[1])
            }
            
            return {
                "parameters": parameters,
                "covariance": pcov,
                "success": True,
                "message": "対数関数フィット成功"
            }
        
        except Exception as e:
            return {
                "parameters": {},
                "covariance": None,
                "success": False,
                "message": f"フィットエラー: {str(e)}"
            }
    
    def predict(self, x: np.ndarray, parameters: dict[str, float]) -> np.ndarray:
        """予測値を計算
        
        Args:
            x: X値の配列
            parameters: フィットパラメータ
            
        Returns:
            np.ndarray: 予測Y値
        """
        a = parameters["a"]
        b = parameters["b"]
        return a + b * np.log(x)

