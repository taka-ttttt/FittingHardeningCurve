"""データモデルのテスト"""

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from app.core.models.dataset import Dataset
from app.core.models.fit_request import FitConfig, FitRequest
from app.core.models.fit_result import FitResult, FitStatistics


class TestDatasetModel:
    """Datasetモデルのテスト"""
    
    def test_valid_dataset(self, sample_dataset):
        """正常なデータセット"""
        assert sample_dataset.id is not None
        assert sample_dataset.filename == "test_data.csv"
        assert not sample_dataset.data.empty
    
    def test_empty_dataframe_validation(self, tmp_path):
        """空のDataFrameは拒否される"""
        with pytest.raises(ValidationError):
            Dataset(
                id="test-id",
                filename="empty.csv",
                filepath=tmp_path / "empty.csv",
                data=pd.DataFrame()
            )
    
    def test_get_xy_data(self, sample_dataset):
        """XYデータ取得"""
        x, y = sample_dataset.get_xy_data()
        
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert len(x) == len(y)
        assert len(x) > 0


class TestFitConfigModel:
    """FitConfigモデルのテスト"""
    
    def test_poly_config(self):
        """多項式設定"""
        config = FitConfig(method='poly', poly_degree=3)
        
        assert config.method == 'poly'
        assert config.poly_degree == 3
    
    def test_invalid_poly_degree(self):
        """無効な次数"""
        with pytest.raises(ValidationError):
            FitConfig(method='poly', poly_degree=0)  # 1以上が必要
    
    def test_exp_config(self):
        """指数関数設定"""
        config = FitConfig(method='exp')
        
        assert config.method == 'exp'


class TestFitResultModel:
    """FitResultモデルのテスト"""
    
    def test_fit_result_creation(self):
        """フィット結果の作成"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = FitResult(
            id='test-id',
            dataset_id='dataset-id',
            config=FitConfig(method='poly', poly_degree=1),
            parameters={'a0': 0.0, 'a1': 2.0},
            statistics=FitStatistics(
                r_squared=1.0,
                adjusted_r_squared=1.0,
                rmse=0.0,
                mae=0.0,
                max_error=0.0,
                aic=0.0,
                bic=0.0,
                residual_sum_squares=0.0,
                total_sum_squares=0.0
            ),
            x_data=x,
            y_data=y,
            y_fitted=y,
            residuals=np.zeros_like(y),
            success=True
        )
        
        assert result.success
        assert result.statistics.r_squared == 1.0
    
    def test_get_fit_function_str(self):
        """関数文字列の取得"""
        result = FitResult(
            id='test-id',
            dataset_id='dataset-id',
            config=FitConfig(method='poly', poly_degree=2),
            parameters={'a0': 1.0, 'a1': 2.0, 'a2': 0.5},
            statistics=FitStatistics(
                r_squared=1.0,
                adjusted_r_squared=1.0,
                rmse=0.0,
                mae=0.0,
                max_error=0.0,
                aic=0.0,
                bic=0.0,
                residual_sum_squares=0.0,
                total_sum_squares=0.0
            ),
            x_data=np.array([1, 2, 3]),
            y_data=np.array([1, 2, 3]),
            y_fitted=np.array([1, 2, 3]),
            residuals=np.array([0, 0, 0]),
            success=True
        )
        
        func_str = result.get_fit_function_str()
        
        assert isinstance(func_str, str)
        assert 'y' in func_str

