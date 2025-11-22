"""指数関数フィッティング"""

from typing import Any

import numpy as np
from scipy.optimize import curve_fit

from app.core.fitting.base import BaseFitter
from app.core.models.fit_request import FitConfig


class ExponentialFitter(BaseFitter):
    """指数関数フィッター
    
    モデル: y = a * exp(b * x) + c
    """
    
    def fit(self, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """指数関数フィッティングを実行
        
        Args:
            x: X値の配列
            y: Y値の配列
            
        Returns:
            dict: フィット結果
        """
        def exp_func(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
            """指数関数"""
            return a * np.exp(b * x) + c
        
        try:
            # 初期値の推定
            if self.config.initial_params:
                p0 = [
                    self.config.initial_params.get("a", 1.0),
                    self.config.initial_params.get("b", 0.1),
                    self.config.initial_params.get("c", 0.0)
                ]
            else:
                # 簡易的な初期値推定
                y_min = np.min(y)
                y_max = np.max(y)
                a_init = y_max - y_min
                b_init = 0.1 if y[-1] > y[0] else -0.1
                c_init = y_min
                p0 = [a_init, b_init, c_init]
            
            # 重み付け
            sigma = None
            if self.config.use_weights and self.config.weights is not None:
                # curve_fitはsigma=1/weightを使用
                sigma = 1.0 / np.array(self.config.weights)
            
            # curve_fitで最適化
            popt, pcov = curve_fit(
                exp_func, x, y,
                p0=p0,
                sigma=sigma,
                absolute_sigma=True,
                maxfev=self.config.max_iterations
            )
            
            parameters = {
                "a": float(popt[0]),
                "b": float(popt[1]),
                "c": float(popt[2])
            }
            
            return {
                "parameters": parameters,
                "covariance": pcov,
                "success": True,
                "message": "指数関数フィット成功"
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
        c = parameters["c"]
        return a * np.exp(b * x) + c

