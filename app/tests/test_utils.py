"""ユーティリティ関数のテスト"""

import numpy as np
import pytest

from app.core.utils.fileio import generate_unique_id, sanitize_filename
from app.core.utils.stats import (
    calculate_aic,
    calculate_bic,
    calculate_mae,
    calculate_r_squared,
    calculate_rmse,
    detect_outliers_iqr,
    detect_outliers_zscore,
)


class TestStatsUtils:
    """統計関数のテスト"""
    
    def test_r_squared(self):
        """R²計算のテスト"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.0, 2.9, 4.1, 5.0])
        
        r2 = calculate_r_squared(y_true, y_pred)
        
        assert 0 <= r2 <= 1
        assert r2 > 0.9
    
    def test_rmse(self):
        """RMSE計算のテスト"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.0, 2.9, 4.1, 5.0])
        
        rmse = calculate_rmse(y_true, y_pred)
        
        assert rmse > 0
        assert rmse < 0.2
    
    def test_mae(self):
        """MAE計算のテスト"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.0, 2.9, 4.1, 5.0])
        
        mae = calculate_mae(y_true, y_pred)
        
        assert mae > 0
        assert mae < 0.2
    
    def test_aic(self):
        """AIC計算のテスト"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.0, 2.9, 4.1, 5.0])
        
        aic = calculate_aic(y_true, y_pred, n_params=2)
        
        assert isinstance(aic, float)
    
    def test_bic(self):
        """BIC計算のテスト"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.0, 2.9, 4.1, 5.0])
        
        bic = calculate_bic(y_true, y_pred, n_params=2)
        
        assert isinstance(bic, float)
    
    def test_outliers_iqr(self):
        """IQR外れ値検出のテスト"""
        data = np.array([1, 2, 2, 3, 3, 3, 4, 4, 5, 100])
        
        outliers = detect_outliers_iqr(data)
        
        assert outliers[-1]  # 100は外れ値
        assert not outliers[0]  # 1は外れ値でない
    
    def test_outliers_zscore(self):
        """Z-score外れ値検出のテスト"""
        data = np.array([1, 2, 2, 3, 3, 3, 4, 4, 5, 100])
        
        outliers = detect_outliers_zscore(data)
        
        assert outliers[-1]  # 100は外れ値
        assert not outliers[0]  # 1は外れ値でない


class TestFileIOUtils:
    """ファイルIO関数のテスト"""
    
    def test_generate_unique_id(self):
        """一意ID生成のテスト"""
        id1 = generate_unique_id()
        id2 = generate_unique_id()
        
        assert isinstance(id1, str)
        assert len(id1) > 0
        assert id1 != id2
    
    def test_sanitize_filename(self):
        """ファイル名サニタイズのテスト"""
        dangerous = 'test<file>:name?.txt'
        safe = sanitize_filename(dangerous)
        
        assert '<' not in safe
        assert '>' not in safe
        assert ':' not in safe
        assert '?' not in safe
        assert safe.endswith('.txt')
    
    def test_sanitize_long_filename(self):
        """長いファイル名のテスト"""
        long_name = 'a' * 300 + '.txt'
        safe = sanitize_filename(long_name)
        
        assert len(safe) <= 205  # max_length + extension

