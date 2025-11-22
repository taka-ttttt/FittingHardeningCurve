"""Pytestの設定とフィクスチャ"""

import numpy as np
import pandas as pd
import pytest

from app.core.models.dataset import Dataset
from app.core.utils.fileio import generate_unique_id


@pytest.fixture
def sample_linear_data():
    """線形データのサンプル"""
    x = np.linspace(0, 10, 50)
    y = 2.5 * x + 1.3 + np.random.randn(50) * 0.5
    return x, y


@pytest.fixture
def sample_quadratic_data():
    """2次関数データのサンプル"""
    x = np.linspace(-5, 5, 50)
    y = 0.5 * x**2 - 2 * x + 3 + np.random.randn(50) * 0.5
    return x, y


@pytest.fixture
def sample_exponential_data():
    """指数関数データのサンプル"""
    x = np.linspace(0, 3, 50)
    y = 2 * np.exp(0.5 * x) + np.random.randn(50) * 0.3
    return x, y


@pytest.fixture
def sample_dataframe():
    """サンプルDataFrame"""
    return pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2.1, 4.2, 6.1, 8.0, 10.2]
    })


@pytest.fixture
def sample_dataset(sample_dataframe, tmp_path):
    """サンプルDataset"""
    filepath = tmp_path / "test_data.csv"
    sample_dataframe.to_csv(filepath, index=False)
    
    return Dataset(
        id=generate_unique_id(),
        filename="test_data.csv",
        filepath=filepath,
        data=sample_dataframe
    )

