"""フィッティング結果関連のモデル"""

from datetime import datetime
from typing import Any

import numpy as np
from pydantic import BaseModel, Field, field_serializer, field_validator

from app.core.models.fit_request import FitConfig


class FitStatistics(BaseModel):
    """フィット統計情報"""
    
    r_squared: float = Field(description="決定係数 R²")
    adjusted_r_squared: float = Field(description="調整済み決定係数")
    rmse: float = Field(description="二乗平均平方根誤差")
    mae: float = Field(description="平均絶対誤差")
    max_error: float = Field(description="最大誤差")
    aic: float = Field(description="赤池情報量規準")
    bic: float = Field(description="ベイズ情報量規準")
    residual_sum_squares: float = Field(description="残差平方和")
    total_sum_squares: float = Field(description="全平方和")


class FitResult(BaseModel):
    """フィッティング結果"""
    
    model_config = {"arbitrary_types_allowed": True}
    
    id: str = Field(description="結果ID")
    name: str | None = Field(default=None, description="結果名")
    description: str | None = Field(default=None, description="結果説明")
    dataset_id: str = Field(description="使用したデータセットID")
    config: FitConfig = Field(description="使用した設定")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # フィット結果
    parameters: dict[str, float] = Field(description="フィットパラメータ")
    parameter_errors: dict[str, float] | None = Field(
        default=None,
        description="パラメータの標準誤差"
    )
    covariance_matrix: np.ndarray | None = Field(
        default=None,
        description="共分散行列"
    )
    
    # 統計情報
    statistics: FitStatistics = Field(description="統計指標")
    
    # データ
    x_data: np.ndarray = Field(description="使用したX値")
    y_data: np.ndarray = Field(description="使用したY値（実測値）")
    y_fitted: np.ndarray = Field(description="フィット値")
    residuals: np.ndarray = Field(description="残差")
    
    # 成功フラグ
    success: bool = Field(default=True, description="フィット成功")
    message: str | None = Field(default=None, description="メッセージ/エラー内容")
    
    @field_validator("x_data", "y_data", "y_fitted", "residuals", "covariance_matrix", mode="before")
    @classmethod
    def convert_to_array(cls, value: Any) -> np.ndarray | None:
        """リストをNumPy配列に変換（デシリアライズ用）"""
        if value is None:
            return None
        if isinstance(value, np.ndarray):
            return value
        return np.array(value)
    
    @field_serializer("x_data", "y_data", "y_fitted", "residuals", "covariance_matrix")
    def serialize_array(self, value: np.ndarray | None, _info: Any) -> list[float] | None:
        """NumPy配列をリストにシリアライズ"""
        if value is None:
            return None
        return value.tolist()
    
    def get_fit_function_str(self) -> str:
        """フィット関数の文字列表現を取得
        
        Returns:
            str: 関数の文字列表現（例: "y = 2.5*x^2 + 1.3*x + 0.5"）
        """
        method = self.config.method
        params = self.parameters
        
        if method == "ludwik":
            # Ludwik硬化則: σ = σ₀ + K * ε^n
            sigma_0 = params.get("σ₀", 0)
            K = params.get("K", 0)
            n = params.get("n", 0)
            return f"σ = {sigma_0:.4g} + {K:.4g} * ε^{n:.4g}"
        
        elif method == "swift":
            # Swift硬化則: σ = K * (ε₀ + ε)^n
            K = params.get("K", 0)
            epsilon_0 = params.get("ε₀", 0)
            n = params.get("n", 0)
            return f"σ = {K:.4g} * ({epsilon_0:.4g} + ε)^{n:.4g}"
        
        elif method == "voce":
            # Voce硬化則: σ = σ₀ + (σ∞ - σ₀) * (1 - exp(-C * ε))
            sigma_0 = params.get("σ₀", 0)
            sigma_inf = params.get("σ∞", 0)
            C = params.get("C", 0)
            return f"σ = {sigma_0:.4g} + ({sigma_inf:.4g} - {sigma_0:.4g}) * (1 - exp(-{C:.4g} * ε))"
        
        else:
            return "カスタム関数"
    
    def predict(self, x: np.ndarray) -> np.ndarray:
        """新しいX値に対する予測値を計算
        
        Args:
            x: X値の配列
            
        Returns:
            np.ndarray: 予測Y値
        """
        method = self.config.method
        params = self.parameters
        
        if method == "ludwik":
            # Ludwik硬化則: σ = σ₀ + K * ε^n
            sigma_0 = params.get("σ₀", 0)
            K = params.get("K", 0)
            n = params.get("n", 0)
            return sigma_0 + K * np.power(x, n)
        
        elif method == "swift":
            # Swift硬化則: σ = K * (ε₀ + ε)^n
            K = params.get("K", 0)
            epsilon_0 = params.get("ε₀", 0)
            n = params.get("n", 0)
            return K * np.power(epsilon_0 + x, n)
        
        elif method == "voce":
            # Voce硬化則: σ = σ₀ + (σ∞ - σ₀) * (1 - exp(-C * ε))
            sigma_0 = params.get("σ₀", 0)
            sigma_inf = params.get("σ∞", 0)
            C = params.get("C", 0)
            return sigma_0 + (sigma_inf - sigma_0) * (1 - np.exp(-C * x))
        
        else:
            raise NotImplementedError(f"Method '{method}' not implemented for prediction")

