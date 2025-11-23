"""フィッティング実行ページ"""

from typing import Any

import numpy as np
import plotly.graph_objects as go
from nicegui import ui

from app.core.models.dataset import Dataset
from app.core.models.fit_request import FitConfig, FitRequest
from app.core.models.fit_result import FitResult
from app.core.services.datasets import DatasetService
from app.core.services.exports import ExportService
from app.core.services.fitting import FittingService
from app.settings import settings
from app.ui.components.charts import create_statistics_card
from app.ui.layout import create_card, create_loading_spinner, navigate_to, show_notification


# 型エイリアス
PageRefs = dict[str, Any]


def render() -> None:
    """フィットページをレンダリング"""
    
    # サービス初期化
    dataset_service = DatasetService(settings.upload_dir)
    fitting_service = FittingService(settings.fits_dir)
    
    # データセット取得
    dataset = dataset_service.get_current_dataset()
    
    with ui.column().classes('w-full max-w-6xl mx-auto p-6 gap-6'):
        ui.label('カーブフィッティング').classes('text-3xl font-bold text-primary mb-2')
        ui.label('モデルを選択してフィッティングを実行します').classes('text-grey-7 mb-4')
        
        if dataset is None:
            _render_no_dataset_state()
            return
        
        # 参照を保持するための辞書
        refs: PageRefs = {
            'dataset': dataset,
            'fitting_service': fitting_service,
            'result_container': None,
            'method_select': None,
            'bounds_inputs': {},
            'range_inputs': {},
            'meta_inputs': {},
            'data_graph': {'fig': None, 'plot': None},
            'current_result': None,
        }
        
        # 2カラムレイアウト
        with ui.row().classes('w-full gap-6 items-start'):
            # 左側：フィッティング設定パネル
            with ui.column().classes('overflow-auto').style('width: 35%; max-height: calc(100vh - 250px);'):
                _render_settings_panel(dataset, refs)
            
            # 右側：グラフ表示エリア
            with ui.column().classes('gap-4 overflow-auto').style('flex: 1; max-height: calc(100vh - 250px);') as result_container:
                refs['result_container'] = result_container
                _render_initial_data_graph(dataset, refs)


def _render_no_dataset_state() -> None:
    """データセットがない状態を表示"""
    with create_card('データがありません', 'warning'):
        ui.label('先にデータをアップロードしてください').classes('text-lg mb-4')
        ui.button(
            'アップロードページへ',
            icon='upload',
            on_click=lambda: navigate_to('/upload')
        ).props('color=primary')


def _render_settings_panel(dataset: Dataset, refs: PageRefs) -> None:
    """設定パネルをレンダリング"""
    with create_card('フィッティング設定', 'settings'):
        # モデル選択（パラメータ設定も含む）
        _render_model_selector(refs)
        
        ui.separator().classes('my-4')
        
        # フィット範囲指定
        _render_range_selector(dataset, refs)
        
        ui.separator().classes('my-4')
        
        # グラフ表示設定
        _render_graph_display_settings(refs)
        
        ui.separator().classes('my-4')
        
        # 実行ボタン
        ui.button(
            'フィッティング実行',
            icon='play_arrow',
            on_click=lambda: _handle_fitting_execution(refs)
        ).props('color=primary size=lg').classes('w-full')


def _render_model_selector(refs: PageRefs) -> None:
    """モデル選択UIをレンダリング"""
    ui.label('モデル選択（複数選択可）').classes('font-bold text-lg mb-2')
    ui.label('フィッティングしたいモデルにチェックを入れてください').classes('text-sm text-grey-7 mb-3')
    
    # 選択状態を管理する辞書
    model_checkboxes: dict[str, ui.checkbox] = {}
    refs['model_checkboxes'] = model_checkboxes
    
    # モデルごとのパラメータ設定コンテナを保持
    model_containers: dict[str, ui.column] = {}
    refs['model_containers'] = model_containers
    
    # 各モデルのチェックボックスとパラメータ設定
    _render_model_card('ludwik', 'Ludwik硬化則', model_checkboxes, model_containers, refs, default_checked=True)
    _render_model_card('swift', 'Swift硬化則', model_checkboxes, model_containers, refs, default_checked=False)
    _render_model_card('voce', 'Voce硬化則', model_checkboxes, model_containers, refs, default_checked=False)


def _render_model_card(
    method: str,
    display_name: str,
    checkboxes_dict: dict[str, ui.checkbox],
    containers_dict: dict[str, ui.column],
    refs: PageRefs,
    default_checked: bool = False
) -> None:
    """各モデルのカードをレンダリング"""
    with ui.card().classes('w-full p-3 mb-3'):
        with ui.row().classes('w-full items-start gap-3'):
            # チェックボックス
            checkbox = ui.checkbox('', value=default_checked).classes('mt-1')
            checkboxes_dict[method] = checkbox
            
            with ui.column().classes('flex-1 gap-2'):
                # モデル名と数式
                ui.label(display_name).classes('font-bold text-base')
                _render_model_description(method)
                
                # パラメータ設定コンテナ（初期は表示/非表示を制御）
                param_container = ui.column().classes('w-full mt-2')
                containers_dict[method] = param_container
                
                # 初期表示設定
                if default_checked:
                    with param_container:
                        _render_model_parameters(method, refs)
                else:
                    param_container.set_visibility(False)
                
                # チェックボックス変更時の処理
                def on_check_change(e, m=method, c=param_container):
                    if e.value:
                        c.set_visibility(True)
                        c.clear()
                        with c:
                            _render_model_parameters(m, refs)
                    else:
                        c.set_visibility(False)
                        c.clear()
                
                checkbox.on_value_change(on_check_change)


def _render_model_description(method: str) -> None:
    """モデルの説明を表示"""
    if method == 'ludwik':
        ui.label('σ = σ₀ + K × ε^n').classes('text-sm text-grey-7 font-mono')
        ui.label('σ₀: 初期応力, K: 硬化係数, n: 硬化指数').classes('text-xs text-grey-6')
    elif method == 'swift':
        ui.label('σ = K × (ε₀ + ε)^n').classes('text-sm text-grey-7 font-mono')
        ui.label('K: 硬化係数, ε₀: 初期ひずみ, n: 硬化指数').classes('text-xs text-grey-6')
    elif method == 'voce':
        ui.label('σ = σ₀ + (σ∞ - σ₀) × (1 - exp(-C × ε))').classes('text-sm text-grey-7 font-mono')
        ui.label('σ₀: 初期応力, σ∞: 飽和応力, C: 硬化係数').classes('text-xs text-grey-6')


def _render_model_parameters(method: str, refs: PageRefs) -> None:
    """各モデルのパラメータ設定UIをレンダリング"""
    # モデルごとのbounds_inputsを初期化（存在しない場合）
    if 'bounds_inputs' not in refs:
        refs['bounds_inputs'] = {}
    
    bounds_inputs = refs['bounds_inputs']
    
    # このモデル専用の入力辞書を作成
    if method not in bounds_inputs:
        bounds_inputs[method] = {}
    
    model_inputs = bounds_inputs[method]
        
    if method == 'ludwik':
        ui.label('※ σ₀（初期応力）はひずみ=0時点の応力値で自動固定されます').classes('text-xs text-orange-6 mb-2')
        _render_constraint_inputs('K (硬化係数, MPa)', f'{method}_K', 0, 5000, '500-2000 MPa', model_inputs)
        _render_constraint_inputs('n (硬化指数)', f'{method}_n', 0, 1, '0.1-0.5', model_inputs, format='%.3f', step=0.01)
        
    elif method == 'swift':
        _render_constraint_inputs('K (硬化係数, MPa)', f'{method}_K', 0, 5000, '500-2000 MPa', model_inputs)
        _render_constraint_inputs('ε₀ (初期ひずみ)', f'{method}_eps0', 0, 0.1, '0.001-0.05', model_inputs, format='%.4f', step=0.001)
        _render_constraint_inputs('n (硬化指数)', f'{method}_n', 0, 1, '0.1-0.5', model_inputs, format='%.3f', step=0.01)
        
    elif method == 'voce':
        ui.label('※ σ₀（初期応力）はひずみ=0時点の応力値で自動固定されます').classes('text-xs text-orange-6 mb-2')
        _render_constraint_inputs('σ∞ (飽和応力, MPa)', f'{method}_sigmainf', 0, 2000, '300-1000 MPa', model_inputs)
        _render_constraint_inputs('C (硬化係数)', f'{method}_C', 0, 100, '5-50', model_inputs)


def _render_constraint_inputs(
    label: str,
    key_prefix: str,
    min_val: float,
    max_val: float,
    hint: str,
    inputs_dict: dict[str, Any],
    format: str = '%.1f',
    step: float = 0.1
) -> None:
    """パラメータ入力フィールドを描画（3行構成）"""
    with ui.column().classes('w-full mb-3'):
        # 1行目：パラメータ名と目安
        with ui.row().classes('w-full items-center gap-2 mb-1'):
            ui.label(label).classes('font-bold text-sm')
            ui.label(f'※目安: {hint}').classes('text-xs text-blue-6')
        
        # 2行目：範囲設定
        with ui.column().classes('w-full gap-1 mb-1').style('flex-wrap: nowrap;'):
            ui.label('範囲設定:').classes('text-xs text-grey-7').style('flex-shrink: 0;')
            with ui.row().classes('items-center gap-1').style('flex-wrap: nowrap;'):
                inputs_dict[f'{key_prefix}_min'] = ui.number(
                    label='最小',
                    value=min_val,
                    format=format
                ).props('dense outlined').style('width: 80px; flex-shrink: 0;')
                
                ui.label('~').classes('text-grey-7 mx-1').style('flex-shrink: 0;')
                
                inputs_dict[f'{key_prefix}_max'] = ui.number(
                    label='最大',
                    value=max_val,
                    format=format
                ).props('dense outlined').style('width: 80px; flex-shrink: 0;')
        
        # 3行目：フィット値と手動調整値（グリッドレイアウト）
        with ui.grid(columns=2).classes('w-full gap-2'):
            # 左側：フィット値
            with ui.column().classes('gap-1').style('flex-wrap: nowrap;'):
                ui.label('フィット値:').classes('text-xs text-grey-7').style('flex-shrink: 0;')
                inputs_dict[f'{key_prefix}_fitted'] = ui.number(
                    value=0,
                    format=format
                ).props('dense outlined readonly borderless').style('width: 80px; flex-shrink: 0; background-color: transparent;')
            
            # 右側：手動調整値
            with ui.column().classes('gap-1').style('flex-wrap: nowrap;'):
                ui.label('手動調整:').classes('text-xs text-grey-7').style('flex-shrink: 0;')
                manual_input = ui.number(
                    value=0,
                    format=format,
                    step=step
                ).props('dense outlined').style('width: 80px; flex-shrink: 0; background-color: #f5f5f5;')
                manual_input.set_enabled(False)
                inputs_dict[f'{key_prefix}_manual'] = manual_input


def _render_range_selector(dataset: Dataset, refs: PageRefs) -> None:
    """フィット範囲選択UIをレンダリング"""
    ui.label('フィット範囲（ひずみの範囲）').classes('font-bold text-lg mb-2')
    
    # デフォルト範囲を計算
    x_col = dataset.data.columns[0]
    y_col = dataset.data.columns[1] if len(dataset.data.columns) > 1 else dataset.data.columns[0]
    x_data, _ = dataset.get_xy_data(x_col, y_col, dropna=True)
    
    x_min_default = 0.0
    x_max_default = float(np.max(x_data))
    data_min = float(np.min(x_data))
    
    # 範囲表示ラベル
    range_label = ui.label(f'選択範囲: {x_min_default:.6f} ~ {x_max_default:.6f}').classes('text-sm text-blue-7 mb-2')
    
    # ui.rangeスライダー
    strain_range = ui.range(
        min=data_min,
        max=x_max_default,
        value={'min': x_min_default, 'max': x_max_default},
        step=0.0001,
    ).classes('w-full').props('label-always')
    
    refs['range_inputs'] = {'range': strain_range}
    
    # 範囲変更時のコールバック関数（strain_range定義後に設定）
    def on_range_change():
        """範囲スライダーの値が変更された時の処理"""
        try:
            value = strain_range.value
            if isinstance(value, dict) and 'min' in value and 'max' in value:
                range_label.set_text(f'選択範囲: {value["min"]:.6f} ~ {value["max"]:.6f}')
                _update_range_visualization(refs)
        except Exception as e:
            print(f"Range change error: {e}")
    
    strain_range.on_value_change(on_range_change)
    
    ui.label(f'データ範囲: {data_min:.6f} ~ {x_max_default:.6f}').classes('text-sm text-grey-7 mt-2')


def _render_graph_display_settings(refs: PageRefs) -> None:
    """グラフ表示設定UIをレンダリング"""
    ui.label('グラフ表示設定').classes('font-bold text-lg mb-2')
    ui.label('フィッティング曲線の描画範囲と密度を設定します').classes('text-sm text-grey-7 mb-3')
    
    # 設定値を保存する辞書
    display_settings = {}
    
    # ①全体の設定
    with ui.card().classes('w-full p-3 mb-3'):
        ui.label('① 全体の設定').classes('font-bold text-sm mb-2')
        
        with ui.row().classes('w-full gap-2 items-center mb-2'):
            ui.label('ひずみレンジ:').classes('text-xs').style('width: 100px;')
            display_settings['global_min'] = ui.number(
                label='最小',
                value=0.0,
                format='%.2f',
                step=0.1
            ).props('dense outlined').style('width: 80px;')
            ui.label('~').classes('text-grey-7')
            display_settings['global_max'] = ui.number(
                label='最大',
                value=3.0,
                format='%.2f',
                step=0.1
            ).props('dense outlined').style('width: 80px;')
        
        with ui.row().classes('w-full gap-2 items-center'):
            ui.label('ひずみ刻み幅:').classes('text-xs').style('width: 100px;')
            display_settings['global_step'] = ui.number(
                label='刻み幅',
                value=0.1,
                format='%.3f',
                step=0.01,
                min=0.001
            ).props('dense outlined').style('width: 120px;')
    
    # ②詳細部の設定
    with ui.card().classes('w-full p-3 mb-3'):
        ui.label('② 詳細部の設定（低ひずみ域を細かく）').classes('font-bold text-sm mb-2')
        
        with ui.row().classes('w-full gap-2 items-center mb-2'):
            ui.label('ひずみレンジ:').classes('text-xs').style('width: 100px;')
            display_settings['detail_min'] = ui.number(
                label='最小',
                value=0.0,
                format='%.3f',
                step=0.01
            ).props('dense outlined').style('width: 80px;')
            ui.label('~').classes('text-grey-7')
            display_settings['detail_max'] = ui.number(
                label='最大',
                value=0.1,
                format='%.3f',
                step=0.01
            ).props('dense outlined').style('width: 80px;')
        
        with ui.row().classes('w-full gap-2 items-center'):
            ui.label('ひずみ刻み幅:').classes('text-xs').style('width: 100px;')
            display_settings['detail_step'] = ui.number(
                label='刻み幅',
                value=0.005,
                format='%.4f',
                step=0.001,
                min=0.0001
            ).props('dense outlined').style('width: 120px;')
    
    refs['display_settings'] = display_settings
    
    # 設定変更時のコールバック
    def on_display_settings_change():
        """表示設定が変更された時の処理"""
        _update_fit_curves_with_new_settings(refs)
    
    # 各入力フィールドに変更イベントを設定
    for widget in display_settings.values():
        widget.on_value_change(on_display_settings_change)


def _update_fit_curves_with_new_settings(refs: PageRefs) -> None:
    """グラフ表示設定の変更に応じてフィット曲線を再描画"""
    current_results = refs.get('current_results', [])
    dataset = refs.get('dataset')
    graph_data_extended = refs.get('data_graph_extended')
    display_settings = refs.get('display_settings')
    
    # 高ひずみ域グラフの横軸範囲を更新
    if graph_data_extended and graph_data_extended.get('fig') and display_settings:
        fig2 = graph_data_extended['fig']
        plot2 = graph_data_extended['plot']
        
        try:
            global_min = display_settings['global_min'].value
            global_max = display_settings['global_max'].value
            
            # 横軸範囲を更新
            fig2.update_xaxes(range=[global_min, global_max])
            plot2.update()
        except Exception as e:
            print(f"X-axis range update error: {e}")
    
    # フィット曲線がある場合は再描画
    if current_results and dataset:
        _render_fit_results_on_graph(current_results, dataset, refs)
        _update_manual_fit_graph(refs)
        # エクスポートUIを更新（すでに存在する場合は内容を更新）
        _render_curve_export_ui(current_results, refs)


def _generate_strain_data(refs: PageRefs) -> np.ndarray:
    """表示設定に基づいてひずみデータを生成
    
    詳細部の範囲には細かい刻み幅、それ以外には全体の刻み幅を適用
    """
    display_settings = refs.get('display_settings')
    
    if not display_settings:
        # デフォルト値
        return np.linspace(0, 3.0, 300)
    
    try:
        # 設定値を取得
        global_min = display_settings['global_min'].value
        global_max = display_settings['global_max'].value
        global_step = display_settings['global_step'].value
        detail_min = display_settings['detail_min'].value
        detail_max = display_settings['detail_max'].value
        detail_step = display_settings['detail_step'].value
        
        # 詳細部が全体の範囲内にあることを確認
        if detail_min >= detail_max or detail_min < global_min or detail_max > global_max:
            # 詳細部の設定が無効な場合は全体設定のみ使用
            return np.arange(global_min, global_max + global_step, global_step)
        
        # 3つの範囲を生成
        # 1. 詳細部より前（global_min ~ detail_min）
        if global_min < detail_min:
            part1 = np.arange(global_min, detail_min, global_step)
        else:
            part1 = np.array([])
        
        # 2. 詳細部（detail_min ~ detail_max）
        part2 = np.arange(detail_min, detail_max + detail_step, detail_step)
        
        # 3. 詳細部より後（detail_max ~ global_max）
        if detail_max < global_max:
            part3 = np.arange(detail_max + global_step, global_max + global_step, global_step)
        else:
            part3 = np.array([])
        
        # 結合して重複を削除
        strain_data = np.concatenate([part1, part2, part3])
        strain_data = np.unique(strain_data)
        
        return strain_data
        
    except Exception as e:
        print(f"Strain data generation error: {e}")
        return np.linspace(0, 3.0, 300)


def _render_initial_data_graph(dataset: Dataset, refs: PageRefs) -> None:
    """初期データグラフを表示（低ひずみ域と高ひずみ域の2つ）"""
    container = refs['result_container']
    if not container:
        return
        
    container.clear()
    
    with container:
        with create_card('データグラフ', 'bar_chart'):
            try:
                x_col = dataset.data.columns[0]
                y_col = dataset.data.columns[1] if len(dataset.data.columns) > 1 else dataset.data.columns[0]
                x_data, y_data = dataset.get_xy_data(x_col, y_col, dropna=True)
                
                x_min_default = 0.0
                x_max_default = float(np.max(x_data))
                
                # グラフ①：低ひずみ域（データ範囲）
                ui.label('① 低ひずみ域（データ範囲）').classes('font-bold text-sm')
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='markers',
                    name='データ',
                    marker=dict(size=6, opacity=0.6, color='blue')
                ))
                
                fig1.add_vrect(
                    x0=x_min_default,
                    x1=x_max_default,
                    fillcolor="green",
                    opacity=0.1,
                    layer="below",
                    line_width=2,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"フィット範囲: {x_min_default:.4f} ~ {x_max_default:.4f}",
                    annotation_position="top left"
                )
                
                fig1.update_layout(
                    xaxis_title='ひずみ（無次元）',
                    yaxis_title=y_col,
                    height=300,
                    hovermode='closest',
                    margin=dict(l=60, r=20, t=20, b=20),
                    showlegend=True,
                    legend=dict(
                        orientation='v',
                        yanchor='middle',
                        y=0.5,
                        xanchor='left',
                        x=1.02,
                        bgcolor='rgba(255,255,255,0.9)',
                        font=dict(size=10)
                    )
                )
                
                plot1 = ui.plotly(fig1).classes('w-full')
                
                # グラフ②：高ひずみ域（外挿表示）
                ui.label('② 高ひずみ域（外挿表示）').classes('font-bold text-sm mt-2')
                
                # 表示範囲の設定を取得（デフォルトは0~3）
                display_settings = refs.get('display_settings')
                if display_settings:
                    try:
                        x_range_min = display_settings['global_min'].value
                        x_range_max = display_settings['global_max'].value
                    except:
                        x_range_min, x_range_max = 0.0, 3.0
                else:
                    x_range_min, x_range_max = 0.0, 3.0
                
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='markers',
                    name='データ',
                    marker=dict(size=6, opacity=0.6, color='blue')
                ))
                
                fig2.add_vrect(
                    x0=x_min_default,
                    x1=x_max_default,
                    fillcolor="green",
                    opacity=0.1,
                    layer="below",
                    line_width=2,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"フィット範囲: {x_min_default:.4f} ~ {x_max_default:.4f}",
                    annotation_position="top left"
                )
                
                fig2.update_layout(
                    xaxis_title='ひずみ（無次元）',
                    yaxis_title=y_col,
                    xaxis=dict(range=[x_range_min, x_range_max]),  # 設定から横軸範囲を取得
                    height=300,
                    hovermode='closest',
                    margin=dict(l=60, r=20, t=20, b=20),
                    showlegend=True,
                    legend=dict(
                        orientation='v',
                        yanchor='middle',
                        y=0.5,
                        xanchor='left',
                        x=1.02,
                        bgcolor='rgba(255,255,255,0.9)',
                        font=dict(size=10)
                    )
                )
                
                plot2 = ui.plotly(fig2).classes('w-full')
                
                # グラフ参照を保存
                refs['data_graph'] = {'fig': fig1, 'plot': plot1}
                refs['data_graph_extended'] = {'fig': fig2, 'plot': plot2}
                
            except Exception as e:
                ui.label(f'グラフ表示エラー: {str(e)}').classes('text-negative')


def _add_range_shading(fig: go.Figure, refs: PageRefs) -> None:
    """グラフにフィット範囲のシェーディングを追加"""
    range_inputs = refs.get('range_inputs')
    if not range_inputs or 'range' not in range_inputs:
        return
    
    try:
        range_widget = range_inputs['range']
        range_value = range_widget.value
        
        # 値が辞書形式かどうか確認
        if isinstance(range_value, dict):
            min_val = range_value.get('min', 0)
            max_val = range_value.get('max', 0)
        else:
            # フォールバック: range_valueが辞書でない場合
            return
        
        fig.add_vrect(
            x0=min_val,
            x1=max_val,
            fillcolor="green",
            opacity=0.1,
            layer="below",
            line_width=2,
            line_dash="dash",
            line_color="green",
            annotation_text=f"フィット範囲: {min_val:.4f} ~ {max_val:.4f}",
            annotation_position="top left"
        )
    except Exception as e:
        # エラーが発生しても続行
        print(f"Range shading error: {e}")


def _update_range_visualization(refs: PageRefs) -> None:
    """フィット範囲の表示を更新"""
    graph_data = refs.get('data_graph')
    graph_data_extended = refs.get('data_graph_extended')
    
    # グラフ①：低ひずみ域の更新
    if graph_data and graph_data['fig'] and graph_data['plot']:
        fig1 = graph_data['fig']
        plot1 = graph_data['plot']
        
        try:
            # 既存のシェーディングを削除して再追加
            fig1.layout.shapes = ()
            fig1.layout.annotations = ()
            _add_range_shading(fig1, refs)
            
            plot1.update()
        except Exception as e:
            print(f"Range visualization update error (graph 1): {e}")
            import traceback
            traceback.print_exc()
    
    # グラフ②：高ひずみ域の更新
    if graph_data_extended and graph_data_extended['fig'] and graph_data_extended['plot']:
        fig2 = graph_data_extended['fig']
        plot2 = graph_data_extended['plot']
        
        try:
            # 既存のシェーディングを削除して再追加
            fig2.layout.shapes = ()
            fig2.layout.annotations = ()
            _add_range_shading(fig2, refs)
            
            plot2.update()
        except Exception as e:
            print(f"Range visualization update error (graph 2): {e}")
            import traceback
            traceback.print_exc()


def _handle_fitting_execution(refs: PageRefs) -> None:
    """フィッティング実行処理（複数モデル対応）"""
    try:
        dataset: Dataset = refs['dataset']
        fitting_service: FittingService = refs['fitting_service']
        model_checkboxes = refs.get('model_checkboxes')
        range_inputs = refs.get('range_inputs')
        meta_inputs = refs.get('meta_inputs')
        
        if not model_checkboxes or not range_inputs:
            return
        
        # 選択されたモデルを取得
        selected_methods = [method for method, checkbox in model_checkboxes.items() if checkbox.value]
        
        if not selected_methods:
            show_notification('少なくとも1つのモデルを選択してください', type='warning')
            return

        loading = create_loading_spinner(f'{len(selected_methods)}個のモデルをフィッティング中...')
        loading.open()
        
        try:
            # 範囲の値を取得
            range_value = range_inputs['range'].value
            x_range = (range_value['min'], range_value['max'])
            
            x_col = dataset.data.columns[0]
            y_col = dataset.data.columns[1] if len(dataset.data.columns) > 1 else dataset.data.columns[0]
            
            # 各モデルに対してフィッティングを実行
            results: list[FitResult] = []
            for method in selected_methods:
                # 各モデルのパラメータ制約を収集
                param_bounds = _collect_parameter_bounds_for_model(method, refs)
                
                # 設定とリクエスト作成
                config = FitConfig(
                    method=method,
                    param_bounds=param_bounds if param_bounds else None,
                    x_range=x_range
                )
                
                name = meta_inputs['name'].value if meta_inputs and meta_inputs['name'].value else None
                if name and len(selected_methods) > 1:
                    name = f"{name}_{method}"
                
                request = FitRequest(
                    dataset_id=dataset.id,
                    x_column=x_col,
                    y_column=y_col,
                    config=config,
                    name=name,
                    description=meta_inputs['desc'].value if meta_inputs else None
                )
                
                # 実行
                result = fitting_service.execute_fit(dataset, request)
                
                if result.success:
                    results.append(result)
                else:
                    show_notification(f'{method}のフィット失敗: {result.message}', type='warning')
            
            if not results:
                show_notification('すべてのフィッティングが失敗しました', type='negative')
                return
            
            # 結果を保存
            refs['current_results'] = results
            
            # パラメータフィールドを更新（手動調整を有効化）
            _update_parameter_fields_after_fit(results, refs)
            
            # グラフを更新（フィッティング結果を表示）
            _render_fit_results_on_graph(results, dataset, refs)
            
            # エクスポートUIを表示
            _render_curve_export_ui(results, refs)
            
            show_notification(f'{len(results)}個のモデルのフィッティングが完了しました', type='positive')
            
        finally:
            loading.close()
            
    except Exception as e:
        show_notification(f'エラー: {str(e)}', type='negative')
        import traceback
        traceback.print_exc()


def _collect_parameter_bounds_for_model(method: str, refs: PageRefs) -> dict[str, tuple[float, float]]:
    """特定のモデルのパラメータ制約を収集"""
    bounds: dict[str, tuple[float, float]] = {}
    bounds_inputs = refs.get('bounds_inputs', {})
    
    if method not in bounds_inputs:
        return bounds
    
    model_inputs = bounds_inputs[method]
    
    # マッピング定義 (入力キープレフィックス, パラメータ名)
    mappings = []
    if method == 'ludwik':
        mappings = [(f'{method}_K', 'K'), (f'{method}_n', 'n')]
    elif method == 'swift':
        mappings = [(f'{method}_K', 'K'), (f'{method}_eps0', 'ε₀'), (f'{method}_n', 'n')]
    elif method == 'voce':
        mappings = [(f'{method}_sigmainf', 'σ∞'), (f'{method}_C', 'C')]
    
    for prefix, param_name in mappings:
        min_key = f'{prefix}_min'
        max_key = f'{prefix}_max'
        if min_key in model_inputs and max_key in model_inputs:
            bounds[param_name] = (model_inputs[min_key].value, model_inputs[max_key].value)
            
    return bounds


def _update_parameter_fields_after_fit(results: list[FitResult], refs: PageRefs) -> None:
    """フィッティング後にパラメータフィールドを更新"""
    bounds_inputs = refs.get('bounds_inputs', {})
    model_checkboxes = refs.get('model_checkboxes', {})
    
    for result in results:
        method = result.config.method
        
        if method not in bounds_inputs:
            continue
        
        model_inputs = bounds_inputs[method]
        
        # パラメータマッピング
        param_mappings = []
        if method == 'ludwik':
            param_mappings = [
                ('K', f'{method}_K'),
                ('n', f'{method}_n')
            ]
        elif method == 'swift':
            param_mappings = [
                ('K', f'{method}_K'),
                ('ε₀', f'{method}_eps0'),
                ('n', f'{method}_n')
            ]
        elif method == 'voce':
            param_mappings = [
                ('σ∞', f'{method}_sigmainf'),
                ('C', f'{method}_C')
            ]
        
        # 各パラメータのフィールドを更新
        for param_name, key_prefix in param_mappings:
            fitted_value = result.parameters.get(param_name)
            if fitted_value is not None:
                # フィッティング値を表示
                fitted_key = f'{key_prefix}_fitted'
                manual_key = f'{key_prefix}_manual'
                
                if fitted_key in model_inputs:
                    model_inputs[fitted_key].set_value(fitted_value)
                
                # 手動調整値を初期化して有効化
                if manual_key in model_inputs:
                    manual_widget = model_inputs[manual_key]
                    manual_widget.set_value(fitted_value)
                    manual_widget.set_enabled(True)
                    manual_widget.style('background-color: white;')
                    
                    # コールバックが未設定の場合のみ設定（重複防止）
                    if not hasattr(manual_widget, '_callback_set'):
                        manual_widget.on_value_change(lambda e, r=refs: _update_manual_fit_graph(r))
                        manual_widget._callback_set = True


def _render_fit_results_on_graph(results: list[FitResult], dataset: Dataset, refs: PageRefs) -> None:
    """フィッティング結果をグラフに描画（2つのグラフに対応）"""
    graph_data = refs.get('data_graph')
    graph_data_extended = refs.get('data_graph_extended')
    
    colors = ['red', 'green', 'purple', 'orange', 'brown', 'pink']
    
    # 表示用のひずみデータを生成
    x_display = _generate_strain_data(refs)
    
    # グラフ①：低ひずみ域（データ範囲）
    if graph_data and graph_data.get('fig') and graph_data.get('plot'):
        fig1 = graph_data['fig']
        plot1 = graph_data['plot']
        
        # 既存の自動フィットトレースをクリア（データ点と手動調整は保持）
        traces_to_keep = []
        for trace in fig1.data:
            # データ点または手動調整トレースは保持
            if trace.name == 'データ' or '手動調整' in trace.name:
                traces_to_keep.append(trace)
        fig1.data = traces_to_keep
        
        # 各結果のフィット曲線を追加
        for i, result in enumerate(results):
            color = colors[i % len(colors)]
            
            # 元のデータ範囲内のx_displayを使用
            x_in_range = x_display[x_display <= np.max(result.x_data)]
            method = result.config.method
            y_display = _calculate_model_prediction(method, result.parameters, x_in_range)
            
            fig1.add_trace(go.Scatter(
                x=x_in_range,
                y=y_display,
                mode='lines+markers',
                name=f'{result.config.method.upper()} フィット (R²={result.statistics.r_squared:.4f})',
                line=dict(color=color, width=2),
                marker=dict(size=4, color=color)
            ))
        
        plot1.update()
    
    # グラフ②：高ひずみ域（外挿表示）
    if graph_data_extended and graph_data_extended.get('fig') and graph_data_extended.get('plot'):
        fig2 = graph_data_extended['fig']
        plot2 = graph_data_extended['plot']
        
        # 既存の自動フィットトレースをクリア（データ点と手動調整は保持）
        traces_to_keep = []
        for trace in fig2.data:
            # データ点または手動調整トレースは保持
            if trace.name == 'データ' or '手動調整' in trace.name:
                traces_to_keep.append(trace)
        fig2.data = traces_to_keep
        
        # 各結果のフィット曲線を追加（外挿）
        for i, result in enumerate(results):
            color = colors[i % len(colors)]
            
            # 外挿予測値を計算
            method = result.config.method
            y_display = _calculate_model_prediction(method, result.parameters, x_display)
            
            fig2.add_trace(go.Scatter(
                x=x_display,
                y=y_display,
                mode='lines+markers',
                name=f'{result.config.method.upper()} フィット (R²={result.statistics.r_squared:.4f})',
                line=dict(color=color, width=2),
                marker=dict(size=4, color=color)
            ))
        
        plot2.update()


def _render_curve_export_ui(results: list[FitResult], refs: PageRefs) -> None:
    """曲線エクスポート用のUI（チェックボックスとボタン）を表示"""
    # 専用のコンテナを取得または作成
    export_container = refs.get('export_container')
    
    if export_container is None:
        # 初回は新規作成
        container = refs['result_container']
        if not container:
            return
        
        with container:
            with create_card('曲線データのエクスポート', 'download') as export_card:
                export_container = ui.column().classes('w-full')
                refs['export_container'] = export_container
    
    # コンテナの内容をクリアして再構築
    export_container.clear()
    
    with export_container:
        ui.label('エクスポートする曲線を選択してください').classes('text-sm text-grey-7 mb-3')
        
        # チェックボックスを管理する辞書
        curve_checkboxes = {}
        refs['curve_checkboxes'] = curve_checkboxes
        
        with ui.column().classes('w-full gap-2'):
            # 各フィット結果に対してチェックボックスを作成
            for result in results:
                method = result.config.method
                method_upper = method.upper()
                
                # 自動フィット曲線のチェックボックス
                auto_key = f'{method}_auto'
                curve_checkboxes[auto_key] = ui.checkbox(
                    f'{method_upper} - 自動フィット (R²={result.statistics.r_squared:.4f})',
                    value=True
                ).classes('text-sm')
                
                # 手動調整曲線のチェックボックス（手動調整がある場合のみ）
                bounds_inputs = refs.get('bounds_inputs', {})
                if method in bounds_inputs:
                    manual_key = f'{method}_manual'
                    curve_checkboxes[manual_key] = ui.checkbox(
                        f'{method_upper} - 手動調整',
                        value=False
                    ).classes('text-sm')
        
        ui.separator().classes('my-3')
        
        # エクスポートボタン
        with ui.row().classes('gap-2'):
            ui.button(
                'CSV形式でエクスポート',
                icon='file_download',
                on_click=lambda: _export_selected_curves(refs)
            ).props('color=primary')
            
            ui.label('※選択した曲線のデータがCSVファイルでダウンロードされます').classes('text-xs text-grey-6')


def _export_selected_curves(refs: PageRefs) -> None:
    """選択された曲線をCSV形式でエクスポート"""
    import pandas as pd
    import tempfile
    from pathlib import Path
    
    try:
        curve_checkboxes = refs.get('curve_checkboxes', {})
        current_results = refs.get('current_results', [])
        bounds_inputs = refs.get('bounds_inputs', {})
        
        if not curve_checkboxes or not current_results:
            show_notification('エクスポートするデータがありません', type='warning')
            return
        
        # 選択された曲線を確認
        selected_curves = {key: cb for key, cb in curve_checkboxes.items() if cb.value}
        
        if not selected_curves:
            show_notification('少なくとも1つの曲線を選択してください', type='warning')
            return
        
        # ひずみデータを生成
        x_display = _generate_strain_data(refs)
        
        # データフレームを構築
        data_dict = {'strain': x_display}
        
        # 各選択された曲線のデータを追加
        for key, _ in selected_curves.items():
            parts = key.split('_')
            method = parts[0]
            curve_type = parts[1]  # 'auto' or 'manual'
            
            # 対応する結果を検索
            result = None
            for r in current_results:
                if r.config.method == method:
                    result = r
                    break
            
            if not result:
                continue
            
            # 曲線データを計算
            if curve_type == 'auto':
                # 自動フィット
                y_data = _calculate_model_prediction(method, result.parameters, x_display)
                column_name = f'{method.upper()}_auto_fit'
            else:
                # 手動調整
                if method not in bounds_inputs:
                    continue
                model_inputs = bounds_inputs[method]
                manual_params = _get_manual_params(result, method, model_inputs)
                y_data = _calculate_model_prediction(method, manual_params, x_display)
                column_name = f'{method.upper()}_manual_adj'
            
            data_dict[column_name] = y_data
        
        # データフレームを作成
        df = pd.DataFrame(data_dict)
        
        # 一時ファイルにCSVを保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = Path(tmp.name)
        
        # ダウンロード
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'fit_curves_{timestamp}.csv'
        
        ui.download(src=str(tmp_path), filename=filename)
        
        show_notification(f'{len(selected_curves)}本の曲線をエクスポートしました', type='positive')
        
    except Exception as e:
        show_notification(f'エクスポートエラー: {str(e)}', type='negative')
        import traceback
        traceback.print_exc()


def _update_manual_fit_graph(refs: PageRefs) -> None:
    """手動調整値に基づいてグラフを更新（フィッティング曲線は保持、2つのグラフに対応）"""
    graph_data = refs.get('data_graph')
    graph_data_extended = refs.get('data_graph_extended')
    bounds_inputs = refs.get('bounds_inputs', {})
    current_results = refs.get('current_results', [])
    
    if not current_results:
        return
    
    colors = ['red', 'green', 'purple', 'orange', 'brown', 'pink']
    
    # 表示用のひずみデータを生成
    x_display = _generate_strain_data(refs)
    
    # グラフ①：低ひずみ域
    if graph_data and graph_data.get('fig') and graph_data.get('plot'):
        fig1 = graph_data['fig']
        plot1 = graph_data['plot']
        
        # 既存の手動調整トレースを削除
        traces_to_keep = []
        for trace in fig1.data:
            if '手動調整' not in trace.name:
                traces_to_keep.append(trace)
        fig1.data = traces_to_keep
        
        # 各結果に対して手動調整値でグラフを再描画
        for i, result in enumerate(current_results):
            method = result.config.method
            
            if method not in bounds_inputs:
                continue
            
            model_inputs = bounds_inputs[method]
            manual_params = _get_manual_params(result, method, model_inputs)
            
            # 元のデータ範囲内のx_displayを使用
            x_in_range = x_display[x_display <= np.max(result.x_data)]
            y_manual = _calculate_model_prediction(method, manual_params, x_in_range)
            
            color = colors[i % len(colors)]
            fig1.add_trace(go.Scatter(
                x=x_in_range,
                y=y_manual,
                mode='lines+markers',
                name=f'{method.upper()} (手動調整)',
                line=dict(color=color, width=2, dash='dot'),
                marker=dict(size=4, color=color, symbol='diamond')
            ))
        
        plot1.update()
    
    # グラフ②：高ひずみ域（外挿）
    if graph_data_extended and graph_data_extended.get('fig') and graph_data_extended.get('plot'):
        fig2 = graph_data_extended['fig']
        plot2 = graph_data_extended['plot']
        
        # 既存の手動調整トレースを削除
        traces_to_keep = []
        for trace in fig2.data:
            if '手動調整' not in trace.name:
                traces_to_keep.append(trace)
        fig2.data = traces_to_keep
        
        # 各結果に対して手動調整値でグラフを再描画（外挿）
        for i, result in enumerate(current_results):
            method = result.config.method
            
            if method not in bounds_inputs:
                continue
            
            model_inputs = bounds_inputs[method]
            manual_params = _get_manual_params(result, method, model_inputs)
            
            # 外挿表示用のひずみデータを使用
            y_manual_extended = _calculate_model_prediction(method, manual_params, x_display)
            
            color = colors[i % len(colors)]
            fig2.add_trace(go.Scatter(
                x=x_display,
                y=y_manual_extended,
                mode='lines+markers',
                name=f'{method.upper()} (手動調整)',
                line=dict(color=color, width=2, dash='dot'),
                marker=dict(size=4, color=color, symbol='diamond')
            ))
        
        plot2.update()


def _get_manual_params(result: FitResult, method: str, model_inputs: dict) -> dict[str, float]:
    """手動調整パラメータを取得するヘルパー関数"""
    manual_params = {}
    param_mappings = []
    
    if method == 'ludwik':
        if 'σ₀' in result.parameters:
            manual_params['σ₀'] = result.parameters['σ₀']  # 固定値
        param_mappings = [('K', f'{method}_K'), ('n', f'{method}_n')]
    elif method == 'swift':
        param_mappings = [('K', f'{method}_K'), ('ε₀', f'{method}_eps0'), ('n', f'{method}_n')]
    elif method == 'voce':
        if 'σ₀' in result.parameters:
            manual_params['σ₀'] = result.parameters['σ₀']  # 固定値
        param_mappings = [('σ∞', f'{method}_sigmainf'), ('C', f'{method}_C')]
    
    for param_name, key_prefix in param_mappings:
        manual_key = f'{key_prefix}_manual'
        if manual_key in model_inputs:
            manual_params[param_name] = model_inputs[manual_key].value
    
    return manual_params


def _render_multiple_fit_results(results: list[FitResult], dataset: Dataset, refs: PageRefs) -> None:
    """複数のフィッティング結果を表示"""
    container = refs['result_container']
    if not container:
        return
        
    container.clear()
    
    with container:
        # 比較グラフ
        _render_comparison_graph(results, dataset, refs)
        
        # 各モデルの結果を展開可能なカードで表示
        for result in results:
            with ui.expansion(f'{result.config.method.upper()}モデル - R²={result.statistics.r_squared:.4f}', icon='analytics').classes('w-full mb-3'):
                # パラメータ表示
                with ui.card().classes('w-full p-3 mb-2'):
                    ui.label('フィッティングパラメータ').classes('font-bold mb-2')
                    with ui.row().classes('gap-3 flex-wrap'):
                        for param_name, param_value in result.parameters.items():
                            with ui.card().classes('p-2 bg-blue-50'):
                                ui.label(param_name).classes('text-xs text-grey-7')
                                ui.label(f'{param_value:.6g}').classes('text-base font-bold')
                
                # 統計指標
                create_statistics_card(result)
                
                # 個別アクションボタン
                with ui.row().classes('gap-2'):
                    ui.button(
                        '保存',
                        icon='save',
                        on_click=lambda r=result: _save_result(r)
                    ).props('color=primary size=sm')
                    
                    ui.button(
                        'CSV',
                        icon='download',
                        on_click=lambda r=result: _download_csv(r)
                    ).props('color=secondary size=sm')
        
        # 全体アクションボタン
        with ui.row().classes('gap-4 mt-4'):
            ui.button(
                'すべて保存',
                icon='save_all',
                on_click=lambda: _save_all_results(results)
            ).props('color=primary')
            
            ui.button(
                '結果一覧へ',
                icon='folder',
                on_click=lambda: navigate_to('/results')
            ).props('flat')


def _render_fit_result(result: FitResult, dataset: Dataset, refs: PageRefs) -> None:
    """フィッティング結果を表示（単一モデル）"""
    container = refs['result_container']
    if not container:
        return
        
    container.clear()
    
    with container:
        # フィット結果グラフとパラメータ調整
        _render_interactive_fit_card(result, dataset, refs)
        
        # 統計指標
        create_statistics_card(result)
        
        # アクションボタン
        _render_action_buttons(result)


def _render_comparison_graph(results: list[FitResult], dataset: Dataset, refs: PageRefs) -> None:
    """複数モデルの比較グラフを描画"""
    with create_card('フィッティング比較', 'bar_chart'):
        y_col = dataset.data.columns[1] if len(dataset.data.columns) > 1 else dataset.data.columns[0]
        
        fig = go.Figure()
        
        # データ点（1回だけ描画）
        if results:
            fig.add_trace(go.Scatter(
                x=results[0].x_data,
                y=results[0].y_data,
                mode='markers',
                name='データ',
                marker=dict(size=8, opacity=0.6, color='blue')
            ))
        
        # 各モデルのフィット曲線
        colors = ['red', 'green', 'purple', 'orange', 'brown', 'pink']
        for i, result in enumerate(results):
            color = colors[i % len(colors)]
            fig.add_trace(go.Scatter(
                x=result.x_data,
                y=result.y_fitted,
                mode='lines',
                name=f'{result.config.method.upper()} (R²={result.statistics.r_squared:.4f})',
                line=dict(color=color, width=2)
            ))
        
        # 使用範囲のシェーディング
        range_inputs = refs.get('range_inputs')
        if range_inputs and 'range' in range_inputs:
            range_value = range_inputs['range'].value
            min_val = range_value['min']
            max_val = range_value['max']
            fig.add_vrect(
                x0=min_val,
                x1=max_val,
                fillcolor="yellow",
                opacity=0.1,
                layer="below",
                line_width=1,
                line_dash="dash",
                line_color="orange"
            )
        
        fig.update_layout(
            xaxis_title='ひずみ（無次元）',
            yaxis_title=y_col,
            yaxis=dict(rangemode='tozero'),
            height=500,
            hovermode='closest',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1.0,
                bgcolor='rgba(255,255,255,0.9)'
            )
        )
        
        ui.plotly(fig).classes('w-full')
        
        # モデル比較テーブル
        ui.label('モデル比較').classes('font-bold text-lg mt-4 mb-2')
        with ui.row().classes('w-full gap-2'):
            for result in results:
                with ui.card().classes('flex-1 p-3'):
                    ui.label(result.config.method.upper()).classes('font-bold text-base mb-2')
                    ui.label(f'R² = {result.statistics.r_squared:.6f}').classes('text-sm')
                    ui.label(f'RMSE = {result.statistics.rmse:.4f}').classes('text-sm')


def _save_all_results(results: list[FitResult]) -> None:
    """すべての結果を保存"""
    try:
        export_service = ExportService(settings.fits_dir)
        saved_count = 0
        
        for result in results:
            try:
                export_service.export_result_json(result)
                export_service.export_result_csv(result)
                saved_count += 1
            except Exception as e:
                print(f"Failed to save {result.config.method}: {e}")
        
        show_notification(f'{saved_count}個の結果を保存しました', type='positive')
    except Exception as e:
        show_notification(f'保存エラー: {str(e)}', type='negative')


def _render_interactive_fit_card(result: FitResult, dataset: Dataset, refs: PageRefs) -> None:
    """インタラクティブなフィット結果カードを表示"""
    with create_card('フィット結果', 'analytics'):
        ui.label('フィッティングパラメータ（手動調整可能）').classes('text-sm font-bold mb-2')
        
        # パラメータ入力とグラフ更新ロジック
        param_inputs = _render_parameter_inputs(result)
        
        # グラフ描画
        fig, plot = _render_result_graph(result, dataset, refs)
        
        # 更新関数を定義
        def update_manual_fit() -> None:
            manual_params = {name: inp.value for name, inp in param_inputs.items()}
            y_manual = _calculate_model_prediction(
                result.config.method, 
                manual_params, 
                result.x_data
            )
            # 手動調整トレース（index 2）を更新
            fig.data[2].y = y_manual
            plot.update()

        # 入力変更時に更新関数を呼び出す
        for inp in param_inputs.values():
            inp.on_value_change(update_manual_fit)


def _render_parameter_inputs(result: FitResult) -> dict[str, ui.number]:
    """パラメータ入力フィールドをレンダリング"""
    param_inputs: dict[str, ui.number] = {}
    
    with ui.row().classes('gap-3 mb-4'):
        for param_name, param_value in result.parameters.items():
            with ui.card().classes('p-2'):
                ui.label(param_name).classes('text-xs text-grey-7 mb-1')
                
                # パラメータに応じた設定
                step, fmt = _get_parameter_format(param_name)
                
                param_inputs[param_name] = ui.number(
                    value=param_value,
                    format=fmt,
                    step=step,
                ).classes('w-24').props('dense')
                
    return param_inputs


def _get_parameter_format(param_name: str) -> tuple[float, str]:
    """パラメータ名に応じたフォーマットを返す"""
    if param_name in ['σ₀', 'K', 'σ∞']:
        return 1.0, '%.2f'
    elif param_name in ['ε₀']:
        return 0.01, '%.4f'
    elif param_name in ['n', 'C']:
        return 0.01, '%.3f'
    else:
        return 0.01, '%.6g'


def _render_result_graph(
    result: FitResult, 
    dataset: Dataset, 
    refs: PageRefs
) -> tuple[go.Figure, ui.plotly]:
    """結果グラフを描画"""
    y_col = dataset.data.columns[1] if len(dataset.data.columns) > 1 else dataset.data.columns[0]
    
    fig = go.Figure()
    
    # データ点
    fig.add_trace(go.Scatter(
        x=result.x_data,
        y=result.y_data,
        mode='markers',
        name='データ',
        marker=dict(size=8, opacity=0.6, color='blue')
    ))
    
    # 元のフィット曲線
    fig.add_trace(go.Scatter(
        x=result.x_data,
        y=result.y_fitted,
        mode='lines',
        name='自動フィット',
        line=dict(color='green', width=1, dash='dash'),
        opacity=0.5
    ))
    
    # 手動調整用曲線（初期状態は自動フィットと同じ）
    fig.add_trace(go.Scatter(
        x=result.x_data,
        y=result.y_fitted,
        mode='lines',
        name='手動調整',
        line=dict(color='red', width=2)
    ))
    
    # 使用範囲のシェーディング
    range_inputs = refs.get('range_inputs')
    if range_inputs and 'range' in range_inputs:
        range_value = range_inputs['range'].value
        min_val = range_value['min']
        max_val = range_value['max']
        fig.add_vrect(
            x0=min_val,
            x1=max_val,
            fillcolor="yellow",
            opacity=0.1,
            layer="below",
            line_width=2,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"使用範囲: {min_val:.4f}~{max_val:.4f}",
            annotation_position="top left"
        )
    
    fig.update_layout(
        xaxis_title='ひずみ（無次元）',
        yaxis_title=y_col,
        yaxis=dict(rangemode='tozero'),
        height=400,
        hovermode='closest',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1.0,
            bgcolor='rgba(255,255,255,0.9)'
        )
    )
    
    plot = ui.plotly(fig).classes('w-full')
    return fig, plot


def _calculate_model_prediction(
    method: str, 
    params: dict[str, float], 
    x_data: np.ndarray
) -> np.ndarray:
    """モデル予測値を計算"""
    if method == 'ludwik':
        sigma_0 = params.get('σ₀', 0)
        K = params.get('K', 0)
        n = params.get('n', 0)
        return sigma_0 + K * np.power(x_data, n)
        
    elif method == 'swift':
        K = params.get('K', 0)
        epsilon_0 = params.get('ε₀', 0)
        n = params.get('n', 0)
        return K * np.power(epsilon_0 + x_data, n)
        
    elif method == 'voce':
        sigma_0 = params.get('σ₀', 0)
        sigma_inf = params.get('σ∞', 0)
        C = params.get('C', 0)
        return sigma_0 + (sigma_inf - sigma_0) * (1 - np.exp(-C * x_data))
        
    return np.zeros_like(x_data)


def _render_action_buttons(result: FitResult) -> None:
    """アクションボタンを表示"""
    with ui.row().classes('gap-4 mt-6'):
        ui.button(
            '結果を保存',
            icon='save',
            on_click=lambda: _save_result(result)
        ).props('color=primary')
        
        ui.button(
            'CSVダウンロード',
            icon='download',
            on_click=lambda: _download_csv(result)
        ).props('color=secondary')
        
        ui.button(
            '結果一覧へ',
            icon='folder',
            on_click=lambda: navigate_to('/results')
        ).props('flat')


def _save_result(result: FitResult) -> None:
    """結果を保存"""
    try:
        export_service = ExportService(settings.fits_dir)
        json_path = export_service.export_result_json(result)
        export_service.export_result_csv(result)
        
        show_notification(f'結果を保存しました: {json_path.name}', type='positive')
    except Exception as e:
        show_notification(f'保存エラー: {str(e)}', type='negative')


def _download_csv(result: FitResult) -> None:
    """CSVをダウンロード"""
    try:
        export_service = ExportService(settings.fits_dir)
        csv_path = export_service.export_result_csv(result)
        filename = f"{result.name or result.id[:8]}_data.csv"
        
        ui.download(src=str(csv_path), filename=filename)
        show_notification('CSVをダウンロードします', type='positive')
    except Exception as e:
        show_notification(f'ダウンロードエラー: {str(e)}', type='negative')
