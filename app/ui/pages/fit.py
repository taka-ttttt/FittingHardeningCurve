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
            with ui.column().classes('flex-none overflow-auto').style('width: 33%; max-height: calc(100vh - 250px);'):
                _render_settings_panel(dataset, refs)
            
            # 右側：グラフ表示エリア
            with ui.column().classes('flex-1 gap-4 overflow-auto').style('max-height: calc(100vh - 250px);') as result_container:
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
        # モデル選択
        _render_model_selector(refs)
        
        ui.separator().classes('my-4')
        
        # パラメータ制約設定
        _render_parameter_constraints(refs)
        
        ui.separator().classes('my-4')
        
        # フィット範囲指定
        _render_range_selector(dataset, refs)
        
        ui.separator().classes('my-4')
        
        # 結果情報入力
        _render_result_meta_inputs(refs)
        
        ui.separator().classes('my-4')
        
        # 実行ボタン
        ui.button(
            'フィッティング実行',
            icon='play_arrow',
            on_click=lambda: _handle_fitting_execution(refs)
        ).props('color=primary size=lg').classes('w-full')


def _render_model_selector(refs: PageRefs) -> None:
    """モデル選択UIをレンダリング"""
    ui.label('モデル選択').classes('font-bold text-lg mb-2')
    
    method_select = ui.select(
        {
            'ludwik': 'Ludwik硬化則',
            'swift': 'Swift硬化則',
            'voce': 'Voce硬化則'
        },
        value='ludwik',
        label='硬化則モデル'
    ).classes('w-full')
    
    refs['method_select'] = method_select
    
    # モデル説明コンテナ
    model_info_container = ui.column().classes('mt-2')
    
    def update_info() -> None:
        model_info_container.clear()
        with model_info_container:
            _render_model_description(method_select.value)
        
        # モデル変更時にパラメータ制約UIも更新
        _update_parameter_constraints_ui(refs)

    method_select.on_value_change(update_info)
    
    # 初期表示
    with model_info_container:
        _render_model_description(method_select.value)


def _render_model_description(method: str) -> None:
    """モデルの説明を表示"""
    if method == 'ludwik':
        ui.label('Ludwik硬化則: σ = σ₀ + K × ε^n').classes('text-sm text-grey-7')
        ui.label('σ₀: 初期応力, K: 硬化係数, n: 硬化指数').classes('text-xs text-grey-6')
    elif method == 'swift':
        ui.label('Swift硬化則: σ = K × (ε₀ + ε)^n').classes('text-sm text-grey-7')
        ui.label('K: 硬化係数, ε₀: 初期ひずみ, n: 硬化指数').classes('text-xs text-grey-6')
    elif method == 'voce':
        ui.label('Voce硬化則: σ = σ₀ + (σ∞ - σ₀) × (1 - exp(-C × ε))').classes('text-sm text-grey-7')
        ui.label('σ₀: 初期応力, σ∞: 飽和応力, C: 硬化係数').classes('text-xs text-grey-6')


def _render_parameter_constraints(refs: PageRefs) -> None:
    """パラメータ制約設定UIをレンダリング"""
    ui.label('パラメータ制約（オプション）').classes('font-bold text-lg mb-2')
    
    # コンテナを作成して参照を保存
    container = ui.column().classes('w-full')
    refs['constraints_container'] = container
    
    # 初期表示
    _update_parameter_constraints_ui(refs)


def _update_parameter_constraints_ui(refs: PageRefs) -> None:
    """パラメータ制約UIの内容を更新"""
    container = refs.get('constraints_container')
    method_select = refs.get('method_select')
    
    if not container or not method_select:
        return
        
    container.clear()
    bounds_inputs: dict[str, Any] = {}
    refs['bounds_inputs'] = bounds_inputs
    
    method = method_select.value
    
    with container:
        ui.label('パラメータ範囲を設定（空欄の場合は自動設定）').classes('text-sm text-grey-7 mb-2')
        
        if method == 'ludwik':
            ui.label('※ σ₀（初期応力）はひずみ=0時点の応力値で自動固定されます').classes('text-xs text-orange-6 mb-2')
            _render_constraint_inputs('K (硬化係数, MPa)', 'K', 0, 5000, '500-2000 MPa', bounds_inputs)
            _render_constraint_inputs('n (硬化指数)', 'n', 0, 1, '0.1-0.5', bounds_inputs, format='%.3f')
            
        elif method == 'swift':
            _render_constraint_inputs('K (硬化係数, MPa)', 'K', 0, 5000, '500-2000 MPa', bounds_inputs)
            _render_constraint_inputs('ε₀ (初期ひずみ)', 'eps0', 0, 0.1, '0.001-0.05', bounds_inputs, format='%.4f')
            _render_constraint_inputs('n (硬化指数)', 'n', 0, 1, '0.1-0.5', bounds_inputs, format='%.3f')
            
        elif method == 'voce':
            ui.label('※ σ₀（初期応力）はひずみ=0時点の応力値で自動固定されます').classes('text-xs text-orange-6 mb-2')
            _render_constraint_inputs('σ∞ (飽和応力, MPa)', 'sigmainf', 0, 2000, '300-1000 MPa', bounds_inputs)
            _render_constraint_inputs('C (硬化係数)', 'C', 0, 100, '5-50', bounds_inputs)


def _render_constraint_inputs(
    label: str,
    key_prefix: str,
    min_val: float,
    max_val: float,
    hint: str,
    inputs_dict: dict[str, Any],
    format: str = '%.1f'
) -> None:
    """制約入力フィールドのペアを描画"""
    with ui.expansion(label, icon='info').classes('w-full mb-2'):
        ui.label(f'金属材料の目安: {hint}').classes('text-xs text-blue-6 mb-2')
        with ui.row().classes('gap-2 w-full'):
            inputs_dict[f'{key_prefix}_min'] = ui.number(label='最小値', value=min_val, format=format).classes('flex-1')
            inputs_dict[f'{key_prefix}_max'] = ui.number(label='最大値', value=max_val, format=format).classes('flex-1')


def _render_range_selector(dataset: Dataset, refs: PageRefs) -> None:
    """フィット範囲選択UIをレンダリング"""
    ui.label('フィット範囲（ひずみの範囲）').classes('font-bold text-lg mb-2')
    
    # デフォルト範囲を計算
    x_col = dataset.data.columns[0]
    y_col = dataset.data.columns[1] if len(dataset.data.columns) > 1 else dataset.data.columns[0]
    x_data, _ = dataset.get_xy_data(x_col, y_col, dropna=True)
    
    x_min_default = 0.0
    x_max_default = float(np.max(x_data))
    
    with ui.row().classes('gap-2 w-full mb-4'):
        strain_min = ui.number(
            label='最小ひずみ',
            value=x_min_default,
            format='%.6f',
            step=0.0001,
            on_change=lambda: _update_range_visualization(refs)
        ).classes('flex-1')
        
        strain_max = ui.number(
            label='最大ひずみ',
            value=x_max_default,
            format='%.6f',
            step=0.0001,
            on_change=lambda: _update_range_visualization(refs)
        ).classes('flex-1')
    
    refs['range_inputs'] = {'min': strain_min, 'max': strain_max}
    
    ui.label(f'データの最大ひずみ: {x_max_default:.6f}').classes('text-sm text-grey-7 mb-2')


def _render_result_meta_inputs(refs: PageRefs) -> None:
    """結果メタ情報入力UIをレンダリング"""
    name_input = ui.input(
        label='結果名（任意）',
        placeholder='例: 実験データ_20250113'
    ).classes('w-full')
    
    desc_input = ui.textarea(
        label='説明（任意）',
        placeholder='フィッティングに関するメモ'
    ).classes('w-full')
    
    refs['meta_inputs'] = {'name': name_input, 'desc': desc_input}


def _render_initial_data_graph(dataset: Dataset, refs: PageRefs) -> None:
    """初期データグラフを表示"""
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
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='markers',
                    name='データ',
                    marker=dict(size=6, opacity=0.6, color='blue')
                ))
                
                # フィット範囲のシェーディングを追加
                _add_range_shading(fig, refs)
                
                fig.update_layout(
                    xaxis_title='ひずみ（無次元）',
                    yaxis_title=y_col,
                    height=400,
                    hovermode='closest',
                    title='フィッティング対象データ'
                )
                
                plot = ui.plotly(fig).classes('w-full')
                
                # グラフ参照を保存
                refs['data_graph'] = {'fig': fig, 'plot': plot}
                
            except Exception as e:
                ui.label(f'グラフ表示エラー: {str(e)}').classes('text-negative')


def _add_range_shading(fig: go.Figure, refs: PageRefs) -> None:
    """グラフにフィット範囲のシェーディングを追加"""
    range_inputs = refs.get('range_inputs')
    if not range_inputs:
        return
        
    min_val = range_inputs['min'].value
    max_val = range_inputs['max'].value
    
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


def _update_range_visualization(refs: PageRefs) -> None:
    """フィット範囲の表示を更新"""
    graph_data = refs.get('data_graph')
    if not graph_data or not graph_data['fig'] or not graph_data['plot']:
        return
    
    fig = graph_data['fig']
    plot = graph_data['plot']
    
    # 既存のシェーディングを削除して再追加
    fig.layout.shapes = ()
    fig.layout.annotations = ()
    _add_range_shading(fig, refs)
    
    plot.update()


def _handle_fitting_execution(refs: PageRefs) -> None:
    """フィッティング実行処理"""
    try:
        dataset: Dataset = refs['dataset']
        fitting_service: FittingService = refs['fitting_service']
        method_select = refs.get('method_select')
        range_inputs = refs.get('range_inputs')
        meta_inputs = refs.get('meta_inputs')
        
        if not method_select or not range_inputs:
            return

        loading = create_loading_spinner('フィッティング中...')
        loading.open()
        
        try:
            # パラメータ制約の収集
            param_bounds = _collect_parameter_bounds(refs)
            
            # 設定とリクエスト作成
            config = FitConfig(
                method=method_select.value,
                param_bounds=param_bounds if param_bounds else None,
                x_range=(range_inputs['min'].value, range_inputs['max'].value)
            )
            
            x_col = dataset.data.columns[0]
            y_col = dataset.data.columns[1] if len(dataset.data.columns) > 1 else dataset.data.columns[0]
            
            request = FitRequest(
                dataset_id=dataset.id,
                x_column=x_col,
                y_column=y_col,
                config=config,
                name=meta_inputs['name'].value if meta_inputs else None,
                description=meta_inputs['desc'].value if meta_inputs else None
            )
            
            # 実行
            result = fitting_service.execute_fit(dataset, request)
            
            if not result.success:
                show_notification(f'フィット失敗: {result.message}', type='negative')
                return
            
            # 結果を保存
            refs['current_result'] = result
            
            # 結果表示
            _render_fit_result(result, dataset, refs)
            show_notification('フィッティングが完了しました', type='positive')
            
        finally:
            loading.close()
            
    except Exception as e:
        show_notification(f'エラー: {str(e)}', type='negative')


def _collect_parameter_bounds(refs: PageRefs) -> dict[str, tuple[float, float]]:
    """入力フィールドからパラメータ制約を収集"""
    bounds: dict[str, tuple[float, float]] = {}
    inputs = refs.get('bounds_inputs', {})
    method = refs['method_select'].value
    
    # マッピング定義
    # (入力プレフィックス, パラメータ名)
    mappings = []
    if method == 'ludwik':
        mappings = [('K', 'K'), ('n', 'n')]
    elif method == 'swift':
        mappings = [('K', 'K'), ('eps0', 'ε₀'), ('n', 'n')]
    elif method == 'voce':
        mappings = [('sigmainf', 'σ∞'), ('C', 'C')]
    
    for prefix, param_name in mappings:
        min_key = f'{prefix}_min'
        max_key = f'{prefix}_max'
        if min_key in inputs and max_key in inputs:
            bounds[param_name] = (inputs[min_key].value, inputs[max_key].value)
            
    return bounds


def _render_fit_result(result: FitResult, dataset: Dataset, refs: PageRefs) -> None:
    """フィッティング結果を表示"""
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
    if range_inputs:
        min_val = range_inputs['min'].value
        max_val = range_inputs['max'].value
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
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
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
