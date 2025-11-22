"""フィッティングエンジンのテスト"""

import numpy as np
import pytest

from app.core.exceptions import DataValidationError, FittingError
from app.core.fitting.exp import ExponentialFitter
from app.core.fitting.log import LogarithmicFitter
from app.core.fitting.poly import PolynomialFitter
from app.core.fitting.power import PowerFitter
from app.core.fitting.registry import FitterRegistry
from app.core.models.fit_request import FitConfig


class TestPolynomialFitter:
    """多項式フィッターのテスト"""
    
    def test_linear_fit(self, sample_linear_data):
        """線形フィット"""
        x, y = sample_linear_data
        
        config = FitConfig(method='poly', poly_degree=1)
        fitter = PolynomialFitter(config)
        
        result = fitter.execute(x, y, 'test-id', 'dataset-id')
        
        assert result.success
        assert 'a0' in result.parameters
        assert 'a1' in result.parameters
        assert result.statistics.r_squared > 0.9
    
    def test_quadratic_fit(self, sample_quadratic_data):
        """2次フィット"""
        x, y = sample_quadratic_data
        
        config = FitConfig(method='poly', poly_degree=2)
        fitter = PolynomialFitter(config)
        
        result = fitter.execute(x, y, 'test-id', 'dataset-id')
        
        assert result.success
        assert 'a0' in result.parameters
        assert 'a1' in result.parameters
        assert 'a2' in result.parameters
        assert result.statistics.r_squared > 0.9


class TestExponentialFitter:
    """指数関数フィッターのテスト"""
    
    def test_exponential_fit(self, sample_exponential_data):
        """指数フィット"""
        x, y = sample_exponential_data
        
        config = FitConfig(method='exp')
        fitter = ExponentialFitter(config)
        
        result = fitter.execute(x, y, 'test-id', 'dataset-id')
        
        assert result.success
        assert 'a' in result.parameters
        assert 'b' in result.parameters
        assert 'c' in result.parameters
        assert result.statistics.r_squared > 0.8


class TestLogarithmicFitter:
    """対数関数フィッターのテスト"""
    
    def test_logarithmic_fit(self):
        """対数フィット"""
        x = np.linspace(0.1, 10, 50)
        y = 2 + 3 * np.log(x) + np.random.randn(50) * 0.3
        
        config = FitConfig(method='log')
        fitter = LogarithmicFitter(config)
        
        result = fitter.execute(x, y, 'test-id', 'dataset-id')
        
        assert result.success
        assert 'a' in result.parameters
        assert 'b' in result.parameters
        assert result.statistics.r_squared > 0.8


class TestPowerFitter:
    """べき乗関数フィッターのテスト"""
    
    def test_power_fit(self):
        """べき乗フィット"""
        x = np.linspace(0.1, 10, 50)
        y = 2 * np.power(x, 1.5) + np.random.randn(50) * 0.5
        
        config = FitConfig(method='power')
        fitter = PowerFitter(config)
        
        result = fitter.execute(x, y, 'test-id', 'dataset-id')
        
        assert result.success
        assert 'a' in result.parameters
        assert 'b' in result.parameters
        assert result.statistics.r_squared > 0.8


class TestFitterRegistry:
    """フィッターレジストリのテスト"""
    
    def test_registry_create_ludwik(self):
        """Registryからludwikフィッターを生成"""
        config = FitConfig(method='ludwik')
        fitter = FitterRegistry.create(config)
        
        assert fitter is not None
        assert fitter.config.method == 'ludwik'
    
    def test_registry_create_swift(self):
        """Registryからswiftフィッターを生成"""
        config = FitConfig(method='swift')
        fitter = FitterRegistry.create(config)
        
        assert fitter is not None
        assert fitter.config.method == 'swift'
    
    def test_registry_create_voce(self):
        """Registryからvoceフィッターを生成"""
        config = FitConfig(method='voce')
        fitter = FitterRegistry.create(config)
        
        assert fitter is not None
        assert fitter.config.method == 'voce'
    
    def test_registry_unknown_method(self):
        """未登録のメソッドでエラー"""
        config = FitConfig(method='ludwik')  # 型チェックのため有効な値を使用
        config.method = 'unknown_method'  # 実行時に無効な値を設定
        
        with pytest.raises(ValueError) as exc_info:
            FitterRegistry.create(config)
        
        assert "未対応のフィッティングメソッド" in str(exc_info.value)
    
    def test_registry_get_available_methods(self):
        """利用可能なメソッド一覧を取得"""
        methods = FitterRegistry.get_available_methods()
        
        assert 'ludwik' in methods
        assert 'swift' in methods
        assert 'voce' in methods
        assert 'poly' in methods
        assert 'exp' in methods
        assert 'log' in methods
        assert 'power' in methods
    
    def test_registry_is_registered(self):
        """メソッドの登録確認"""
        assert FitterRegistry.is_registered('ludwik') is True
        assert FitterRegistry.is_registered('swift') is True
        assert FitterRegistry.is_registered('unknown') is False

