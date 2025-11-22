"""統計計算ユーティリティ"""

import numpy as np


def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """決定係数R²を計算
    
    Args:
        y_true: 実測値
        y_pred: 予測値
        
    Returns:
        float: R²値
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
    
    return float(1 - (ss_res / ss_tot))


def calculate_adjusted_r_squared(
    r_squared: float,
    n_samples: int,
    n_params: int
) -> float:
    """調整済みR²を計算
    
    Args:
        r_squared: R²値
        n_samples: サンプル数
        n_params: パラメータ数
        
    Returns:
        float: 調整済みR²値
    """
    if n_samples <= n_params + 1:
        return r_squared
    
    return float(1 - (1 - r_squared) * (n_samples - 1) / (n_samples - n_params - 1))


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """二乗平均平方根誤差（RMSE）を計算
    
    Args:
        y_true: 実測値
        y_pred: 予測値
        
    Returns:
        float: RMSE値
    """
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """平均絶対誤差（MAE）を計算
    
    Args:
        y_true: 実測値
        y_pred: 予測値
        
    Returns:
        float: MAE値
    """
    return float(np.mean(np.abs(y_true - y_pred)))


def calculate_aic(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_params: int
) -> float:
    """赤池情報量規準（AIC）を計算
    
    Args:
        y_true: 実測値
        y_pred: 予測値
        n_params: パラメータ数
        
    Returns:
        float: AIC値
    """
    n = len(y_true)
    rss = np.sum((y_true - y_pred) ** 2)
    
    if rss <= 0:
        return float('-inf')
    
    return float(n * np.log(rss / n) + 2 * n_params)


def calculate_bic(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_params: int
) -> float:
    """ベイズ情報量規準（BIC）を計算
    
    Args:
        y_true: 実測値
        y_pred: 予測値
        n_params: パラメータ数
        
    Returns:
        float: BIC値
    """
    n = len(y_true)
    rss = np.sum((y_true - y_pred) ** 2)
    
    if rss <= 0:
        return float('-inf')
    
    return float(n * np.log(rss / n) + n_params * np.log(n))


def detect_outliers_iqr(
    data: np.ndarray,
    multiplier: float = 1.5
) -> np.ndarray:
    """IQR法で外れ値を検出
    
    Args:
        data: データ配列
        multiplier: IQR倍率（デフォルト1.5）
        
    Returns:
        np.ndarray: 外れ値のブール配列
    """
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    return (data < lower_bound) | (data > upper_bound)


def detect_outliers_zscore(
    data: np.ndarray,
    threshold: float = 3.0
) -> np.ndarray:
    """Z-score法で外れ値を検出
    
    Args:
        data: データ配列
        threshold: 閾値（デフォルト3.0）
        
    Returns:
        np.ndarray: 外れ値のブール配列
    """
    mean = np.mean(data)
    std = np.std(data)
    
    if std == 0:
        return np.zeros(len(data), dtype=bool)
    
    z_scores = np.abs((data - mean) / std)
    return z_scores > threshold


def calculate_confidence_interval(
    mean: float,
    std_error: float,
    confidence_level: float = 0.95
) -> tuple[float, float]:
    """信頼区間を計算
    
    Args:
        mean: 平均値
        std_error: 標準誤差
        confidence_level: 信頼水準（デフォルト0.95）
        
    Returns:
        tuple: (下限, 上限)
    """
    from scipy import stats
    
    # t分布の臨界値（自由度は大きいと仮定してz値を使用）
    z = stats.norm.ppf((1 + confidence_level) / 2)
    margin = z * std_error
    
    return (mean - margin, mean + margin)

