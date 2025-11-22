"""サンプルCSVデータ生成スクリプト

様々なパターンのテストデータを生成します。
"""

import numpy as np
import pandas as pd
from pathlib import Path


def generate_polynomial_data(
    n_points: int = 50,
    degree: int = 3,
    noise_level: float = 0.1,
    x_range: tuple[float, float] = (0, 10)
) -> pd.DataFrame:
    """多項式データを生成"""
    np.random.seed(42)
    x = np.linspace(x_range[0], x_range[1], n_points)
    
    # ランダムな係数を生成
    coeffs = np.random.randn(degree + 1) * 10
    y = np.polyval(coeffs, x)
    
    # ノイズを追加
    noise = np.random.randn(n_points) * noise_level * np.abs(y).mean()
    y_noisy = y + noise
    
    return pd.DataFrame({'x': x, 'y': y_noisy})


def generate_exponential_data(
    n_points: int = 50,
    a: float = 2.0,
    b: float = 0.5,
    noise_level: float = 0.1,
    x_range: tuple[float, float] = (0, 5)
) -> pd.DataFrame:
    """指数関数データを生成 (y = a * exp(b * x))"""
    np.random.seed(42)
    x = np.linspace(x_range[0], x_range[1], n_points)
    y = a * np.exp(b * x)
    
    noise = np.random.randn(n_points) * noise_level * np.abs(y).mean()
    y_noisy = y + noise
    
    return pd.DataFrame({'x': x, 'y': y_noisy})


def generate_logarithmic_data(
    n_points: int = 50,
    a: float = 5.0,
    b: float = 2.0,
    noise_level: float = 0.1,
    x_range: tuple[float, float] = (0.1, 10)
) -> pd.DataFrame:
    """対数関数データを生成 (y = a + b * ln(x))"""
    np.random.seed(42)
    x = np.linspace(x_range[0], x_range[1], n_points)
    y = a + b * np.log(x)
    
    noise = np.random.randn(n_points) * noise_level * np.abs(y).mean()
    y_noisy = y + noise
    
    return pd.DataFrame({'x': x, 'y': y_noisy})


def generate_power_data(
    n_points: int = 50,
    a: float = 3.0,
    b: float = 1.5,
    noise_level: float = 0.1,
    x_range: tuple[float, float] = (0.1, 10)
) -> pd.DataFrame:
    """べき乗関数データを生成 (y = a * x^b)"""
    np.random.seed(42)
    x = np.linspace(x_range[0], x_range[1], n_points)
    y = a * np.power(x, b)
    
    noise = np.random.randn(n_points) * noise_level * np.abs(y).mean()
    y_noisy = y + noise
    
    return pd.DataFrame({'x': x, 'y': y_noisy})


def generate_stress_strain_data() -> pd.DataFrame:
    """応力-ひずみ曲線データを生成（工学用途）"""
    np.random.seed(42)
    
    # 弾性域
    strain1 = np.linspace(0, 0.002, 20)
    stress1 = 200000 * strain1  # ヤング率 200 GPa
    
    # 降伏～塑性域
    strain2 = np.linspace(0.002, 0.05, 30)
    stress2 = 400 + 5000 * (strain2 - 0.002) ** 0.5
    
    # ネッキング
    strain3 = np.linspace(0.05, 0.08, 20)
    stress3 = stress2[-1] * (1 - (strain3 - 0.05) / 0.05)
    
    strain = np.concatenate([strain1, strain2, strain3])
    stress = np.concatenate([stress1, stress2, stress3])
    
    # ノイズ追加
    noise = np.random.randn(len(stress)) * 20
    stress_noisy = stress + noise
    
    return pd.DataFrame({
        'ひずみ(%)': strain * 100,
        '応力(N/mm²)': stress_noisy
    })


def main():
    """サンプルデータを生成"""
    data_dir = Path(__file__).parent.parent / 'data' / 'uploads'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 各種サンプルデータを生成
    samples = {
        'sample_polynomial.csv': generate_polynomial_data(),
        'sample_exponential.csv': generate_exponential_data(),
        'sample_logarithmic.csv': generate_logarithmic_data(),
        'sample_power.csv': generate_power_data(),
        'sample_stress_strain.csv': generate_stress_strain_data(),
    }
    
    for filename, df in samples.items():
        filepath = data_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f'✓ {filename} を生成しました ({len(df)} 行)')
    
    print(f'\n全てのサンプルファイルを {data_dir} に保存しました。')


if __name__ == '__main__':
    main()

