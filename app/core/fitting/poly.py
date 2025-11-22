"""多項式フィッティング"""

from typing import Any

import numpy as np

from app.core.fitting.base import BaseFitter
from app.core.models.fit_request import FitConfig


class PolynomialFitter(BaseFitter):
    """多項式フィッター"""
    
    def __init__(self, config: FitConfig):
        """初期化
        
        Args:
            config: フィッティング設定
        """
        super().__init__(config)
        if config.poly_degree is None:
            raise ValueError("poly_degreeが必要です")
        self.degree = config.poly_degree
    
    def fit(self, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """多項式フィッティングを実行
        
        Args:
            x: X値の配列
            y: Y値の配列
            
        Returns:
            dict: フィット結果
        """
        try:
            # 重み付け
            weights = None
            if self.config.use_weights and self.config.weights is not None:
                weights = np.array(self.config.weights)
            
            # numpy.polyfitで多項式フィット
            # 次数は degree で、最高次から最低次への係数を返す
            coeffs, residuals, rank, singular_values, rcond = np.polyfit(
                x, y, self.degree, full=True, w=weights
            )
            
            # 共分散行列を計算
            try:
                # Vandermonde行列を構築
                vander = np.vander(x, self.degree + 1)
                if weights is not None:
                    vander = vander * weights[:, np.newaxis]
                
                # 共分散行列 = (V^T V)^-1 * residual_variance
                vander_t_vander = np.dot(vander.T, vander)
                
                if len(residuals) > 0:
                    residual_variance = residuals[0] / (len(x) - self.degree - 1)
                else:
                    # 完全フィットの場合
                    y_pred = np.polyval(coeffs, x)
                    residual_variance = np.sum((y - y_pred)**2) / max(len(x) - self.degree - 1, 1)
                
                covariance = np.linalg.inv(vander_t_vander) * residual_variance
            except np.linalg.LinAlgError:
                covariance = None
            
            # パラメータ辞書を作成（a0, a1, ..., an）
            # coeffsは高次から低次の順なので反転
            parameters = {
                f"a{i}": float(coeffs[self.degree - i])
                for i in range(self.degree + 1)
            }
            
            return {
                "parameters": parameters,
                "covariance": covariance,
                "success": True,
                "message": f"{self.degree}次多項式フィット成功"
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
        # a0 + a1*x + a2*x^2 + ... + an*x^n
        coeffs = [parameters[f"a{i}"] for i in range(self.degree + 1)]
        # numpy.polyvalは高次から低次の順で係数を受け取るので反転
        return np.polyval(coeffs[::-1], x)

