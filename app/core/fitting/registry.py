"""フィッターのレジストリ"""

from typing import Type

from app.core.fitting.base import BaseFitter
from app.core.models.fit_request import FitConfig


class FitterRegistry:
    """フィッター登録・生成クラス
    
    Open-Closed原則に基づき、新規フィッター追加時に
    既存コードの変更を最小化するためのレジストリパターン実装
    """
    
    _registry: dict[str, Type[BaseFitter]] = {}
    
    @classmethod
    def register(cls, method_name: str, fitter_class: Type[BaseFitter]) -> None:
        """フィッターを登録
        
        Args:
            method_name: メソッド名（例: "ludwik", "swift"）
            fitter_class: フィッタークラス
        """
        cls._registry[method_name] = fitter_class
    
    @classmethod
    def create(cls, config: FitConfig) -> BaseFitter:
        """設定に応じたフィッターを生成
        
        Args:
            config: フィッティング設定
            
        Returns:
            BaseFitter: 生成されたフィッター
            
        Raises:
            ValueError: 未登録のメソッドの場合
        """
        fitter_class = cls._registry.get(config.method)
        
        if fitter_class is None:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"未対応のフィッティングメソッド: {config.method}\n"
                f"利用可能なメソッド: {available}"
            )
        
        return fitter_class(config)
    
    @classmethod
    def get_available_methods(cls) -> list[str]:
        """利用可能なメソッド一覧を取得
        
        Returns:
            list[str]: 登録済みメソッド名のリスト
        """
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, method_name: str) -> bool:
        """メソッドが登録済みか確認
        
        Args:
            method_name: メソッド名
            
        Returns:
            bool: 登録済みならTrue
        """
        return method_name in cls._registry

