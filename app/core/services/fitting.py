"""フィッティング実行サービス"""

from pathlib import Path

import numpy as np

from app.core.exceptions import DataValidationError, FittingError
from app.core.fitting.base import BaseFitter
from app.core.fitting.registry import FitterRegistry
from app.core.models.dataset import Dataset
from app.core.models.fit_request import FitConfig, FitRequest
from app.core.models.fit_result import FitResult
from app.core.utils.fileio import ensure_directory, generate_unique_id
from app.core.utils.monitoring import performance_monitor
from app.logging_conf import get_logger

logger = get_logger(__name__)


class FittingService:
    """フィッティング実行サービス"""
    
    def __init__(self, results_dir: Path | str = "data/fits"):
        """初期化
        
        Args:
            results_dir: 結果保存ディレクトリ
        """
        self.results_dir = Path(results_dir)
        ensure_directory(self.results_dir)
    
    def create_fitter(self, config: FitConfig) -> BaseFitter:
        """設定に応じたフィッターを作成
        
        Args:
            config: フィッティング設定
            
        Returns:
            BaseFitter: フィッター
            
        Raises:
            ValueError: 未対応のメソッドの場合
        """
        # Registryパターンを使用して簡潔にフィッターを生成
        return FitterRegistry.create(config)
    
    @performance_monitor
    def execute_fit(
        self,
        dataset: Dataset,
        request: FitRequest
    ) -> FitResult:
        """フィッティングを実行
        
        Args:
            dataset: データセット
            request: フィッティングリクエスト
            
        Returns:
            FitResult: フィット結果
            
        Raises:
            DataValidationError: データが不正な場合
            FittingError: フィッティングに失敗した場合
        """
        logger.info(f"フィッティング開始: method={request.config.method}, dataset={request.dataset_id}")
        
        # データを取得
        try:
            x, y = dataset.get_xy_data(
                x_col=request.x_column,
                y_col=request.y_column,
                dropna=True
            )
        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            raise DataValidationError(f"データ取得に失敗しました: {e}") from e
        
        # データが不十分な場合
        if len(x) < 3:
            error_msg = f"データポイントが不十分です（現在: {len(x)}点、最低3点必要）"
            logger.warning(error_msg)
            return self._create_failed_result(request, error_msg)
        
        # フィッターを作成
        try:
            fitter = self.create_fitter(request.config)
        except ValueError as e:
            logger.error(f"フィッター作成エラー: {e}")
            return self._create_failed_result(request, str(e))
        
        # フィッティング実行
        try:
            result_id = generate_unique_id()
            result = fitter.execute(
                x, y,
                result_id=result_id,
                dataset_id=request.dataset_id,
                name=request.name,
                description=request.description
            )
            
            if result.success:
                logger.info(
                    f"フィッティング成功: R²={result.statistics.r_squared:.4f}, "
                    f"RMSE={result.statistics.rmse:.4f}"
                )
            else:
                logger.warning(f"フィッティング失敗: {result.message}")
            
            return result
            
        except Exception as e:
            logger.error(f"フィッティング実行エラー: {e}", exc_info=True)
            raise FittingError(f"フィッティング実行に失敗しました: {e}") from e
    
    def predict_new_points(
        self,
        result: FitResult,
        x_new: np.ndarray
    ) -> np.ndarray:
        """既存のフィット結果を使って新しい点を予測
        
        Args:
            result: フィット結果
            x_new: 新しいX値
            
        Returns:
            np.ndarray: 予測Y値
        """
        return result.predict(x_new)
    
    @performance_monitor
    def compare_models(
        self,
        dataset: Dataset,
        x_column: str,
        y_column: str,
        configs: list[FitConfig]
    ) -> list[FitResult]:
        """複数のモデルを比較
        
        Args:
            dataset: データセット
            x_column: X列名
            y_column: Y列名
            configs: フィッティング設定のリスト
            
        Returns:
            list[FitResult]: フィット結果のリスト（R²の降順）
        """
        logger.info(f"モデル比較開始: {len(configs)}種類のモデル")
        results = []
        
        for config in configs:
            request = FitRequest(
                dataset_id=dataset.id,
                x_column=x_column,
                y_column=y_column,
                config=config,
                name=f"{config.method}フィット"
            )
            
            try:
                result = self.execute_fit(dataset, request)
                results.append(result)
            except (DataValidationError, FittingError) as e:
                logger.warning(f"モデル {config.method} のフィットをスキップ: {e}")
                continue
        
        # R²でソート（降順）
        results.sort(key=lambda r: r.statistics.r_squared, reverse=True)
        
        if results:
            best = results[0]
            logger.info(
                f"最良モデル: {best.config.method} (R²={best.statistics.r_squared:.4f})"
            )
        
        return results
    
    def calculate_residuals(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> dict[str, np.ndarray]:
        """残差分析
        
        Args:
            y_true: 実測値
            y_pred: 予測値
            
        Returns:
            dict: 残差分析結果
        """
        residuals = y_true - y_pred
        
        # 標準化残差
        std_residuals = residuals / np.std(residuals) if np.std(residuals) > 0 else residuals
        
        return {
            "residuals": residuals,
            "standardized_residuals": std_residuals,
            "absolute_residuals": np.abs(residuals)
        }
    
    def _create_failed_result(
        self,
        request: FitRequest,
        message: str
    ) -> FitResult:
        """失敗結果を作成
        
        Args:
            request: リクエスト
            message: エラーメッセージ
            
        Returns:
            FitResult: 失敗結果
        """
        from app.core.models.fit_result import FitStatistics
        
        return FitResult(
            id=generate_unique_id(),
            name=request.name,
            description=request.description,
            dataset_id=request.dataset_id,
            config=request.config,
            parameters={},
            statistics=FitStatistics(
                r_squared=0, adjusted_r_squared=0, rmse=0, mae=0,
                max_error=0, aic=0, bic=0, residual_sum_squares=0,
                total_sum_squares=0
            ),
            x_data=np.array([]),
            y_data=np.array([]),
            y_fitted=np.array([]),
            residuals=np.array([]),
            success=False,
            message=message
        )

