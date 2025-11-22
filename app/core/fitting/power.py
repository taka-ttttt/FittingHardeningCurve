"""べき乗関数フィッティング"""

from typing import Any

import numpy as np
from scipy.optimize import curve_fit

from app.core.fitting.base import BaseFitter
from app.core.models.fit_request import FitConfig


class PowerFitter(BaseFitter):
    """べき乗関数フィッター
    
    モデル: y = a * x^b
    """
    
    def fit(self, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """べき乗関数フィッティングを実行
        
        Args:
            x: X値の配列
            y: Y値の配列
            
        Returns:
            dict: フィット結果
        """
        # x > 0, y > 0 のチェック
        if np.any(x <= 0):
            return {
                "parameters": {},
                "covariance": None,
                "success": False,
                "message": "べき乗フィットにはx > 0が必要です"
            }
        
        def power_func(x: np.ndarray, a: float, b: float) -> np.ndarray:
            """べき乗関数"""
            return a * np.power(x, b)
        
        try:
            # 初期値
            if self.config.initial_params:
                p0 = [
                    self.config.initial_params.get("a", 1.0),
                    self.config.initial_params.get("b", 1.0)
                ]
            else:
                # 対数線形回帰で初期値推定: ln(y) = ln(a) + b * ln(x)
                # y > 0のデータのみ使用
                mask = y > 0
                if np.sum(mask) < 2:
                    p0 = [1.0, 1.0]
                else:
                    log_x = np.log(x[mask])
                    log_y = np.log(y[mask])
                    coeffs = np.polyfit(log_x, log_y, 1)
                    p0 = [np.exp(coeffs[1]), coeffs[0]]  # [exp(切片), 傾き]
            
            # 重み付け
            sigma = None
            if self.config.use_weights and self.config.weights is not None:
                sigma = 1.0 / np.array(self.config.weights)
            
            # curve_fitで最適化
            popt, pcov = curve_fit(
                power_func, x, y,
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
                "message": "べき乗関数フィット成功"
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
        return a * np.power(x, b)

