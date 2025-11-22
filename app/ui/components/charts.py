"""グラフコンポーネント"""

from typing import Any

import numpy as np
import plotly.graph_objects as go
from nicegui import ui

from app.core.models.fit_result import FitResult


def create_scatter_plot(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str = 'X',
    y_label: str = 'Y',
    title: str = 'データプロット',
    show_line: bool = False
) -> ui.plotly:
    """散布図を作成
    
    Args:
        x: X値
        y: Y値
        x_label: X軸ラベル
        y_label: Y軸ラベル
        title: グラフタイトル
        show_line: 線を表示するか
        
    Returns:
        ui.plotly: Plotlyコンポーネント
    """
    fig = go.Figure()
    
    # 散布図
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        name='データ',
        marker=dict(
            size=8,
            color='royalblue',
            opacity=0.7
        )
    ))
    
    # 線グラフ（オプション）
    if show_line:
        order = np.argsort(x)
        fig.add_trace(go.Scatter(
            x=x[order],
            y=y[order],
            mode='lines',
            name='接続線',
            line=dict(color='lightgray', width=1, dash='dash')
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=500,
        hovermode='closest',
        template='plotly_white'
    )
    
    return ui.plotly(fig).classes('w-full')


def create_fit_plot(
    result: FitResult,
    x_label: str | None = None,
    y_label: str | None = None,
    title: str | None = None,
    show_confidence: bool = False
) -> ui.plotly:
    """フィットプロットを作成
    
    Args:
        result: フィット結果
        x_label: X軸ラベル
        y_label: Y軸ラベル
        title: グラフタイトル
        show_confidence: 信頼区間を表示するか
        
    Returns:
        ui.plotly: Plotlyコンポーネント
    """
    fig = go.Figure()
    
    # 実測値（散布図）
    fig.add_trace(go.Scatter(
        x=result.x_data,
        y=result.y_data,
        mode='markers',
        name='実測値',
        marker=dict(
            size=8,
            color='royalblue',
            opacity=0.7
        )
    ))
    
    # フィット曲線
    # 滑らかな曲線のため、より多くの点を生成
    x_smooth = np.linspace(result.x_data.min(), result.x_data.max(), 200)
    y_smooth = result.predict(x_smooth)
    
    fig.add_trace(go.Scatter(
        x=x_smooth,
        y=y_smooth,
        mode='lines',
        name='フィット曲線',
        line=dict(color='red', width=2)
    ))
    
    # 信頼区間（オプション）
    if show_confidence and result.parameter_errors:
        # 簡易的な信頼区間（標準誤差の2倍）
        # より正確には共分散行列から計算すべき
        pass
    
    # タイトルに関数式を含める
    if title is None:
        title = f'フィット結果<br><sub>{result.get_fit_function_str()}</sub>'
    
    fig.update_layout(
        title=title,
        xaxis_title=x_label or 'X',
        yaxis_title=y_label or 'Y',
        height=500,
        hovermode='closest',
        template='plotly_white',
        showlegend=True
    )
    
    return ui.plotly(fig).classes('w-full')


def create_residual_plot(
    result: FitResult,
    plot_type: str = 'scatter'
) -> ui.plotly:
    """残差プロットを作成
    
    Args:
        result: フィット結果
        plot_type: プロットタイプ（scatter, histogram）
        
    Returns:
        ui.plotly: Plotlyコンポーネント
    """
    fig = go.Figure()
    
    if plot_type == 'scatter':
        # 残差 vs フィット値
        fig.add_trace(go.Scatter(
            x=result.y_fitted,
            y=result.residuals,
            mode='markers',
            marker=dict(
                size=8,
                color='green',
                opacity=0.6
            ),
            name='残差'
        ))
        
        # ゼロ線
        fig.add_trace(go.Scatter(
            x=[result.y_fitted.min(), result.y_fitted.max()],
            y=[0, 0],
            mode='lines',
            line=dict(color='red', width=1, dash='dash'),
            name='ゼロ線'
        ))
        
        fig.update_layout(
            title='残差プロット',
            xaxis_title='フィット値',
            yaxis_title='残差',
            height=400,
            hovermode='closest',
            template='plotly_white'
        )
    
    elif plot_type == 'histogram':
        # 残差のヒストグラム
        fig.add_trace(go.Histogram(
            x=result.residuals,
            nbinsx=30,
            marker=dict(color='green', opacity=0.7),
            name='残差分布'
        ))
        
        fig.update_layout(
            title='残差分布',
            xaxis_title='残差',
            yaxis_title='頻度',
            height=400,
            template='plotly_white'
        )
    
    return ui.plotly(fig).classes('w-full')


def create_comparison_plot(
    results: list[FitResult],
    x_data: np.ndarray,
    y_data: np.ndarray,
    x_label: str = 'X',
    y_label: str = 'Y'
) -> ui.plotly:
    """複数モデルの比較プロットを作成
    
    Args:
        results: フィット結果のリスト
        x_data: 実測X値
        y_data: 実測Y値
        x_label: X軸ラベル
        y_label: Y軸ラベル
        
    Returns:
        ui.plotly: Plotlyコンポーネント
    """
    fig = go.Figure()
    
    # 実測値
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='markers',
        name='実測値',
        marker=dict(
            size=8,
            color='black',
            opacity=0.5
        )
    ))
    
    # 各モデルのフィット曲線
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    x_smooth = np.linspace(x_data.min(), x_data.max(), 200)
    
    for i, result in enumerate(results):
        y_smooth = result.predict(x_smooth)
        color = colors[i % len(colors)]
        
        model_name = f'{result.config.method} (R²={result.statistics.r_squared:.4f})'
        
        fig.add_trace(go.Scatter(
            x=x_smooth,
            y=y_smooth,
            mode='lines',
            name=model_name,
            line=dict(color=color, width=2)
        ))
    
    fig.update_layout(
        title='モデル比較',
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=600,
        hovermode='closest',
        template='plotly_white',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return ui.plotly(fig).classes('w-full')


def create_statistics_card(result: FitResult) -> None:
    """統計情報カードを作成
    
    Args:
        result: フィット結果
    """
    stats = result.statistics
    
    with ui.card().classes('w-full p-4'):
        ui.label('統計指標').classes('text-xl font-bold mb-3')
        
        with ui.grid(columns=2).classes('gap-4 w-full'):
            # R²
            with ui.card().classes('p-3 bg-blue-50'):
                ui.label('R² (決定係数)').classes('text-sm text-grey-7')
                ui.label(f'{stats.r_squared:.6f}').classes('text-2xl font-bold text-blue-700')
            
            # 調整済みR²
            with ui.card().classes('p-3 bg-blue-50'):
                ui.label('調整済みR²').classes('text-sm text-grey-7')
                ui.label(f'{stats.adjusted_r_squared:.6f}').classes('text-2xl font-bold text-blue-700')
            
            # RMSE
            with ui.card().classes('p-3 bg-green-50'):
                ui.label('RMSE').classes('text-sm text-grey-7')
                ui.label(f'{stats.rmse:.6g}').classes('text-2xl font-bold text-green-700')
            
            # MAE
            with ui.card().classes('p-3 bg-green-50'):
                ui.label('MAE').classes('text-sm text-grey-7')
                ui.label(f'{stats.mae:.6g}').classes('text-2xl font-bold text-green-700')
            
            # AIC
            with ui.card().classes('p-3 bg-orange-50'):
                ui.label('AIC').classes('text-sm text-grey-7')
                ui.label(f'{stats.aic:.6g}').classes('text-2xl font-bold text-orange-700')
            
            # BIC
            with ui.card().classes('p-3 bg-orange-50'):
                ui.label('BIC').classes('text-sm text-grey-7')
                ui.label(f'{stats.bic:.6g}').classes('text-2xl font-bold text-orange-700')


def create_parameters_table(result: FitResult) -> None:
    """パラメータテーブルを作成
    
    Args:
        result: フィット結果
    """
    columns = [
        {'name': 'parameter', 'label': 'パラメータ', 'field': 'parameter', 'align': 'left'},
        {'name': 'value', 'label': '値', 'field': 'value', 'align': 'right'},
    ]
    
    rows = []
    for param, value in result.parameters.items():
        row = {
            'parameter': param,
            'value': f'{value:.6g}'
        }
        
        if result.parameter_errors and param in result.parameter_errors:
            error = result.parameter_errors[param]
            row['value'] = f'{value:.6g} ± {error:.6g}'
            columns.append({'name': 'error', 'label': '誤差', 'field': 'error', 'align': 'right'})
            row['error'] = f'{error:.6g}'
        
        rows.append(row)
    
    with ui.card().classes('w-full p-4'):
        ui.label('フィットパラメータ').classes('text-xl font-bold mb-3')
        ui.label(result.get_fit_function_str()).classes('text-lg mb-3 font-mono bg-grey-2 p-2 rounded')
        
        ui.table(
            columns=columns,
            rows=rows,
            row_key='parameter'
        ).classes('w-full')

