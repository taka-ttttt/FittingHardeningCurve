"""フィッティングリクエスト関連のモデル"""

from typing import Any, Literal

from pydantic import BaseModel, Field


# フィッティングメソッドの型定義
FitMethod = Literal["ludwik", "swift", "voce", "poly", "exp", "log", "power"]


class FitConfig(BaseModel):
    """フィッティング設定"""
    
    method: FitMethod = Field(description="フィッティング手法")
    
    # 多項式フィット用パラメータ
    poly_degree: int = Field(
        default=3,
        ge=1,
        le=10,
        description="多項式の次数（polyメソッドの場合のみ使用）"
    )
    
    # パラメータ制約（オプション）
    param_bounds: dict[str, tuple[float, float]] | None = Field(
        default=None,
        description="パラメータの上下限制約 {'param_name': (lower, upper)}"
    )
    
    # 初期値（オプション）
    initial_params: dict[str, float] | None = Field(
        default=None,
        description="パラメータの初期値"
    )
    
    # 重み付け
    use_weights: bool = Field(
        default=False,
        description="重み付けフィットを使用するか"
    )
    
    weights: list[float] | None = Field(
        default=None,
        description="各データポイントの重み"
    )
    
    # フィット範囲制限
    x_range: tuple[float, float] | None = Field(
        default=None,
        description="フィット範囲（x_min, x_max）"
    )
    
    # 計算オプション
    max_iterations: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="最大反復回数"
    )
    
    tolerance: float = Field(
        default=1e-8,
        gt=0,
        description="収束判定の閾値"
    )


class FitRequest(BaseModel):
    """フィッティング実行リクエスト"""
    
    dataset_id: str = Field(description="データセットID")
    x_column: str = Field(description="X軸の列名")
    y_column: str = Field(description="Y軸の列名")
    config: FitConfig = Field(description="フィッティング設定")
    name: str | None = Field(
        default=None,
        description="フィット結果の名前（任意）"
    )
    description: str | None = Field(
        default=None,
        description="フィット結果の説明（任意）"
    )

