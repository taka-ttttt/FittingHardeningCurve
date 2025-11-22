"""データアップロードと前処理ページ"""

from io import BytesIO
from typing import Any

import numpy as np
import plotly.graph_objects as go
from nicegui import events, ui
from plotly.subplots import make_subplots

from app.core.models.dataset import Dataset
from app.core.services.datasets import DatasetService
from app.core.services.preprocessing import PreprocessingService
from app.settings import settings
from app.ui.layout import create_card, navigate_to, show_notification


# 型エイリアス
PageRefs = dict[str, Any]
PreprocessingOptions = dict[str, Any]


def render() -> None:
    """アップロード・前処理ページをレンダリング"""
    
    dataset_service = DatasetService(settings.upload_dir)
    preprocessing_service = PreprocessingService()
    
    # 現在のデータセットを取得
    current_dataset = dataset_service.get_current_dataset()
    
    with ui.column().classes('w-full max-w-6xl mx-auto p-6 gap-6'):
        ui.label('データアップロードと前処理').classes('text-3xl font-bold text-primary mb-2')
        ui.label('CSVファイルをアップロードして、データの前処理を行います').classes('text-grey-7 mb-4')
        
        # 2カラムレイアウト: 左側に設定、右側にグラフ
        with ui.row().classes('w-full gap-6 items-start'):
            # 左側：データ設定パネル
            with ui.column().classes('flex-none overflow-auto').style('width: 33%; max-height: calc(100vh - 250px);') as settings_container:
                # ページ内で共有する参照を保持
                refs: PageRefs = {
                    'graph_container': None,
                    'settings_container': settings_container,
                    'dataset_service': dataset_service,
                    'preprocessing_service': preprocessing_service,
                }
                
                _render_settings_panel(
                    dataset_service,
                    preprocessing_service,
                    current_dataset,
                    settings_container,
                    refs
                )
            
            # 右側：グラフ表示エリア
            with ui.column().classes('flex-1 gap-4 overflow-auto').style('max-height: calc(100vh - 250px);') as graph_container:
                refs['graph_container'] = graph_container
                
                if current_dataset:
                    _render_dataset_graph(current_dataset, graph_container)
                else:
                    _render_empty_graph_state(graph_container)


def _render_settings_panel(
    dataset_service: DatasetService,
    preprocessing_service: PreprocessingService,
    current_dataset: Dataset | None,
    settings_container: ui.column,
    refs: PageRefs
) -> None:
    """設定パネルをレンダリング"""
    
    with create_card('データ設定', 'settings'):
        # ファイル選択UI
        _render_file_upload_ui(refs)
        
        # 設定UIを追加するためのコンテナ（動的に追加・削除可能）
        dataset_settings_container = ui.column().classes('w-full')
        refs['dataset_settings_container'] = dataset_settings_container
        
        # 既存のデータセットがある場合は設定UIを表示
        if current_dataset:
            refs['settings_separator_added'] = True
            _render_dataset_settings(
                current_dataset,
                dataset_service,
                preprocessing_service,
                dataset_settings_container,
                refs
            )


def _render_file_upload_ui(refs: PageRefs) -> None:
    """ファイルアップロードUIをレンダリング"""
    ui.label('ファイル選択').classes('font-bold text-lg mb-2')
    ui.label('CSVファイルを選択してください（最大10MB）').classes('mb-4')
    
    ui.upload(
        on_upload=lambda e: _handle_upload_event(e, refs),
        auto_upload=True,
        label='CSVファイルを選択'
    ).props('accept=".csv" color=primary').classes('w-full')
    
    ui.label('または、ファイルをドラッグ&ドロップ').classes('text-sm text-grey-7 mt-2')


def _render_empty_graph_state(graph_container: ui.column) -> None:
    """グラフエリアの空状態を表示"""
    with create_card('グラフ', 'bar_chart'):
        with ui.column().classes('w-full items-center text-center p-8'):
            ui.icon('info', size='3rem').classes('text-blue-500 mb-4')
            ui.label('CSVファイルをアップロードしてください').classes('text-lg font-bold')
            ui.label('データのグラフがここに表示されます').classes('text-grey-7 mt-2')


def _render_dataset_graph(
    dataset: Dataset, 
    graph_container: ui.column,
    x_col: str | None = None,
    y_col: str | None = None
) -> None:
    """データセットのグラフを表示"""
    graph_container.clear()
    
    # カラムが指定されていない場合は最初の2列を使用
    if x_col is None or y_col is None:
        columns = dataset.data.columns.tolist()
        x_col = columns[0]
        y_col = columns[1] if len(columns) > 1 else columns[0]
    
    with graph_container:
        with create_card('グラフ', 'bar_chart'):
            ui.label('元データ').classes('text-lg font-bold mb-4')
            
            try:
                x, y = dataset.get_xy_data(x_col, y_col, dropna=True)
                _render_scatter_plot(x, y, x_col, y_col, '元データ', 'blue')
            except Exception as e:
                ui.label(f'エラー: {str(e)}').classes('text-negative')


async def _handle_upload_event(
    e: events.UploadEventArguments,
    refs: PageRefs
) -> None:
    """ファイルアップロードイベントを処理"""
    try:
        dataset_service: DatasetService = refs['dataset_service']
        preprocessing_service: PreprocessingService = refs['preprocessing_service']
        graph_container = refs.get('graph_container')
        
        # ファイルサイズチェック
        content = await e.file.read()
        size_mb = len(content) / (1024 * 1024)
        
        if size_mb > settings.max_upload_size:
            show_notification(
                f'ファイルサイズが大きすぎます（{size_mb:.1f}MB > {settings.max_upload_size}MB）',
                type='negative'
            )
            return
        
        # データセット作成
        show_notification('ファイルを読み込んでいます...', type='info')
        
        dataset = await dataset_service.load_from_upload(content, e.file.name)
        dataset_service.set_current_dataset(dataset)
        
        # グラフを更新
        if graph_container:
            _render_dataset_graph(dataset, graph_container)
        
        # 設定UIを動的に追加
        _add_dataset_settings_ui(dataset, dataset_service, preprocessing_service, refs)
        
        show_notification('ファイルを正常に読み込みました', type='positive')
        
    except Exception as ex:
        show_notification(f'エラー: {str(ex)}', type='negative')


def _add_dataset_settings_ui(
    dataset: Dataset,
    dataset_service: DatasetService,
    preprocessing_service: PreprocessingService,
    refs: PageRefs
) -> None:
    """データセット設定UIを動的に追加"""
    dataset_settings_container = refs.get('dataset_settings_container')
    if dataset_settings_container:
        dataset_settings_container.clear()
        
        _render_dataset_settings(
            dataset,
            dataset_service,
            preprocessing_service,
            dataset_settings_container,
            refs
        )


def _render_dataset_settings(
    dataset: Dataset,
    dataset_service: DatasetService,
    preprocessing_service: PreprocessingService,
    settings_container: ui.column,
    refs: PageRefs
) -> None:
    """データセット設定UIをレンダリング"""
    
    columns = dataset.data.columns.tolist()
    x_column = columns[0]
    y_column = columns[1] if len(columns) > 1 else columns[0]
    
    selectors: dict[str, Any] = {}
    
    with settings_container:
        # separatorを追加（まだ存在しない場合）
        if not refs.get('settings_separator_added'):
            ui.separator().classes('my-4')
            refs['settings_separator_added'] = True
        
        # カラム選択UI
        _render_column_selectors(dataset, selectors, refs, x_column, y_column)
        
        ui.separator().classes('my-4')
        
        # 前処理オプションUI
        preprocessing_controls = _render_preprocessing_options()
        
        ui.separator().classes('my-4')
        
        # 実行ボタン
        ui.button(
            '前処理を実行',
            icon='play_arrow',
            on_click=lambda: _handle_preprocessing_execution(
                dataset,
                dataset_service,
                preprocessing_service,
                selectors,
                preprocessing_controls,
                refs
            )
        ).props('color=primary size=lg').classes('w-full')
        
        ui.separator().classes('my-4')
        
        # フィッティングへ
        ui.button(
            'フィッティングページへ',
            icon='trending_up',
            on_click=lambda: navigate_to('/fit')
        ).props('color=secondary').classes('w-full')


def _render_column_selectors(
    dataset: Dataset,
    selectors: dict[str, Any],
    refs: PageRefs,
    x_column: str,
    y_column: str
) -> None:
    """カラム選択UIをレンダリング"""
    columns = dataset.data.columns.tolist()
    
    with ui.column().classes('gap-2 w-full'):
        selectors['x_select'] = ui.select(
            columns,
            label='X軸（ひずみ）',
            value=x_column,
            on_change=lambda: _handle_column_change(dataset, selectors, refs)
        ).classes('w-full')
        
        selectors['y_select'] = ui.select(
            columns,
            label='Y軸（応力）',
            value=y_column,
            on_change=lambda: _handle_column_change(dataset, selectors, refs)
        ).classes('w-full')


def _render_preprocessing_options() -> dict[str, Any]:
    """前処理オプションUIをレンダリングし、コントロールを返す"""
    ui.label('前処理オプション').classes('font-bold text-lg mb-2')
    
    controls: dict[str, Any] = {}
    
    # ひずみ単位変換
    controls['strain_percent'] = ui.checkbox(
        'ひずみ単位を%から無次元に変換',
        value=False
    ).classes('mb-2')
    ui.label('(ε = ε_% / 100)').classes('text-caption text-grey-7 ml-6 -mt-2 mb-3')
    
    # 公称→真変換
    controls['convert_true'] = ui.checkbox(
        '公称ひずみ・応力を真ひずみ・応力に変換',
        value=False
    ).classes('mb-2')
    with ui.column().classes('ml-6 -mt-2 mb-3 text-caption text-grey-7'):
        ui.label('真ひずみ: ε_true = ln(1 + ε_nominal)')
        ui.label('真応力: σ_true = σ_nominal × (1 + ε_nominal)')
    
    # 全ひずみ→塑性ひずみ変換
    controls['convert_plastic'] = ui.checkbox(
        '全ひずみを塑性ひずみに変換',
        value=False
    ).classes('mb-2')
    ui.label('(ε_plastic = ε_total - σ / E)').classes('text-caption text-grey-7 ml-6 -mt-2 mb-3')
    
    # ヤング率と降伏応力の入力
    with ui.column().classes('gap-2 w-full mt-2'):
        controls['youngs_modulus'] = ui.number(
            label='ヤング率 E (MPa)',
            value=200000.0,
            format='%.2f'
        ).classes('w-full')
        
        controls['yield_stress'] = ui.number(
            label='降伏応力 σ_y (MPa)',
            value=200.0,
            format='%.2f'
        ).classes('w-full')
    
    # 塑性ひずみ変換のチェックボックスと入力フィールドの連動
    def toggle_plastic_inputs() -> None:
        enabled = controls['convert_plastic'].value
        controls['youngs_modulus'].set_enabled(enabled)
        controls['yield_stress'].set_enabled(enabled)
    
    controls['youngs_modulus'].set_enabled(False)
    controls['yield_stress'].set_enabled(False)
    controls['convert_plastic'].on_value_change(toggle_plastic_inputs)
    
    return controls


def _handle_column_change(
    dataset: Dataset, 
    selectors: dict[str, Any], 
    refs: PageRefs
) -> None:
    """カラム変更イベントを処理"""
    graph_container = refs.get('graph_container')
    if graph_container:
        x_col = selectors['x_select'].value
        y_col = selectors['y_select'].value
        _render_dataset_graph(dataset, graph_container, x_col, y_col)


def _handle_preprocessing_execution(
    dataset: Dataset,
    dataset_service: DatasetService,
    preprocessing_service: PreprocessingService,
    selectors: dict[str, Any],
    preprocessing_controls: dict[str, Any],
    refs: PageRefs
) -> None:
    """前処理実行イベントを処理"""
    try:
        x_col = selectors['x_select'].value
        y_col = selectors['y_select'].value
        
        # 前処理オプションを取得
        strain_percent = preprocessing_controls['strain_percent'].value
        convert_true = preprocessing_controls['convert_true'].value
        convert_plastic = preprocessing_controls['convert_plastic'].value
        youngs_modulus = preprocessing_controls['youngs_modulus'].value if convert_plastic else None
        yield_stress = preprocessing_controls['yield_stress'].value if convert_plastic else None
        
        # 前処理を実行
        processed_dataset = preprocessing_service.apply_preprocessing(
            dataset=dataset,
            x_column=x_col,
            y_column=y_col,
            strain_unit_percent=strain_percent,
            convert_to_true=convert_true,
            convert_to_plastic=convert_plastic,
            youngs_modulus=youngs_modulus,
            yield_stress=yield_stress,
        )
        
        # 前処理済みデータセットを保存
        dataset_service.save_dataset(processed_dataset)
        dataset_service.set_current_dataset(processed_dataset)
        
        # 前処理オプションを収集
        preprocessing_options: PreprocessingOptions = {
            'strain_percent': strain_percent,
            'convert_true': convert_true,
            'convert_plastic': convert_plastic,
            'youngs_modulus': youngs_modulus,
            'yield_stress': yield_stress,
        }
        
        # グラフを更新
        graph_container = refs.get('graph_container')
        if graph_container:
            _render_preprocessing_comparison(
                dataset,
                processed_dataset,
                x_col,
                y_col,
                preprocessing_options,
                graph_container
            )
        
        show_notification('前処理が完了しました', type='positive')
        
    except Exception as e:
        show_notification(f'エラー: {str(e)}', type='negative')


def _render_scatter_plot(
    x_data: np.ndarray,
    y_data: np.ndarray,
    x_label: str,
    y_label: str,
    name: str,
    color: str = 'blue'
) -> None:
    """散布図を作成してレンダリング"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='markers',
        name=name,
        marker=dict(size=6, opacity=0.6, color=color)
    ))
    
    fig.update_layout(
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=400,
        hovermode='closest'
    )
    
    ui.plotly(fig).classes('w-full')


def _render_preprocessing_comparison(
    original_dataset: Dataset,
    processed_dataset: Dataset,
    x_col: str,
    y_col: str,
    preprocessing_options: PreprocessingOptions,
    graph_container: ui.column
) -> None:
    """前処理前後のデータ比較グラフをレンダリング"""
    graph_container.clear()
    
    # 元データと前処理後データを取得
    original_x, original_y = original_dataset.get_xy_data(x_col, y_col, dropna=True)
    processed_x, processed_y = processed_dataset.get_xy_data(x_col, y_col, dropna=True)
    
    # 軸ラベルを作成（XY両軸をまとめて処理）
    axis_labels = _build_comparison_axis_labels(x_col, y_col, preprocessing_options)
    original_x_label = axis_labels['original_x']
    processed_x_label = axis_labels['processed_x']
    original_y_label = axis_labels['original_y']
    processed_y_label = axis_labels['processed_y']
    
    with graph_container:
        with create_card('グラフ', 'bar_chart'):
            # 縦に並べたサブプロット
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('元データ', '前処理後データ'),
                vertical_spacing=0.15,
                row_heights=[0.5, 0.5]
            )
            
            # 元データ
            fig.add_trace(
                go.Scatter(
                    x=original_x,
                    y=original_y,
                    mode='markers',
                    name='元データ',
                    marker=dict(size=6, opacity=0.6, color='blue')
                ),
                row=1, col=1
            )
            
            # 前処理後データ
            fig.add_trace(
                go.Scatter(
                    x=processed_x,
                    y=processed_y,
                    mode='markers',
                    name='前処理後',
                    marker=dict(size=6, opacity=0.6, color='red')
                ),
                row=2, col=1
            )
            
            # 軸ラベル設定
            fig.update_xaxes(title_text=original_x_label, row=1, col=1)
            fig.update_yaxes(title_text=original_y_label, row=1, col=1)
            fig.update_xaxes(title_text=processed_x_label, row=2, col=1)
            fig.update_yaxes(title_text=processed_y_label, row=2, col=1)
            
            fig.update_layout(
                height=800,
                showlegend=False,
                hovermode='closest'
            )
            
            ui.plotly(fig).classes('w-full')
            
            # 前処理内容の説明
            _render_preprocessing_summary(preprocessing_options)
            
            # 統計情報
            _render_data_statistics(original_x, original_y, processed_x, processed_y)
            
            # エクスポートボタン
            _render_export_button(processed_dataset, x_col, y_col, preprocessing_options)


def _build_comparison_axis_labels(
    x_col: str,
    y_col: str,
    preprocessing_options: PreprocessingOptions
) -> dict[str, str]:
    """前処理前後の比較用にXY軸すべてのラベルを構築
    
    Args:
        x_col: X軸のカラム名
        y_col: Y軸のカラム名
        preprocessing_options: 前処理オプション
        
    Returns:
        dict: 'original_x', 'processed_x', 'original_y', 'processed_y'のキーを持つ辞書
    """
    # X軸ラベル
    original_x = x_col
    processed_x = x_col
    
    if preprocessing_options.get('strain_percent'):
        original_x += ' (%)'
        processed_x += ' (無次元)'
    
    if preprocessing_options.get('convert_true'):
        original_x += ' (公称)'
        processed_x += ' (真)'
    
    if preprocessing_options.get('convert_plastic'):
        original_x += ' (全ひずみ)'
        processed_x += ' (塑性ひずみ)'
    
    # Y軸ラベル
    original_y = y_col
    processed_y = y_col
    
    if preprocessing_options.get('convert_true'):
        original_y += ' (公称)'
        processed_y += ' (真)'
    
    return {
        'original_x': original_x,
        'processed_x': processed_x,
        'original_y': original_y,
        'processed_y': processed_y,
    }


def _render_preprocessing_summary(preprocessing_options: PreprocessingOptions) -> None:
    """適用された前処理の概要を表示"""
    with ui.card().classes('w-full p-4 mt-4 bg-blue-50'):
        ui.label('適用された前処理').classes('text-lg font-bold mb-2')
        with ui.column().classes('gap-1'):
            if preprocessing_options.get('strain_percent'):
                ui.label('✓ ひずみ単位変換: % → 無次元 (ε = ε_% / 100)').classes('text-sm')
            
            if preprocessing_options.get('convert_true'):
                ui.label('✓ 公称 → 真への変換').classes('text-sm')
                ui.label('  - 真ひずみ: ε_true = ln(1 + ε_nominal)').classes('text-sm ml-4 text-grey-7')
                ui.label('  - 真応力: σ_true = σ_nominal × (1 + ε_nominal)').classes('text-sm ml-4 text-grey-7')
            
            if preprocessing_options.get('convert_plastic'):
                youngs_modulus = preprocessing_options.get('youngs_modulus', 0)
                yield_stress = preprocessing_options.get('yield_stress', 0)
                ui.label(
                    f'✓ 全ひずみ → 塑性ひずみ変換 (E = {youngs_modulus} MPa, σ_y = {yield_stress} MPa)'
                ).classes('text-sm')
                ui.label('  - ε_plastic = ε_total - σ / E').classes('text-sm ml-4 text-grey-7')


def _render_data_statistics(
    original_x: np.ndarray,
    original_y: np.ndarray,
    processed_x: np.ndarray,
    processed_y: np.ndarray
) -> None:
    """データの統計情報を表示"""
    with create_card('統計情報', 'analytics'):
        with ui.grid(columns=2).classes('gap-6 w-full'):
            # 元データの統計
            _render_single_dataset_statistics('元データ', original_x, original_y)
            
            # 前処理後データの統計
            _render_single_dataset_statistics('前処理後データ', processed_x, processed_y)


def _render_single_dataset_statistics(
    title: str,
    x_data: np.ndarray,
    y_data: np.ndarray
) -> None:
    """単一データセットの統計情報を表示"""
    with ui.column():
        ui.label(title).classes('text-h6 mb-2')
        
        stats = {
            'データ点数': len(x_data),
            'X範囲': f'{x_data.min():.4f} ~ {x_data.max():.4f}',
            'Y範囲': f'{y_data.min():.4f} ~ {y_data.max():.4f}',
            'X平均': f'{x_data.mean():.4f}',
            'Y平均': f'{y_data.mean():.4f}',
        }
        
        for key, value in stats.items():
            with ui.row().classes('gap-2'):
                ui.label(f'{key}:').classes('font-bold')
                ui.label(str(value))


def _render_export_button(
    dataset: Dataset,
    x_col: str,
    y_col: str,
    preprocessing_options: PreprocessingOptions
) -> None:
    """前処理後のデータをエクスポートするボタンを表示"""
    with ui.card().classes('w-full p-4 mt-4 bg-green-50'):
        ui.label('データのエクスポート').classes('text-lg font-bold mb-2')
        ui.label('前処理後のデータをCSVファイルとしてダウンロードできます').classes('text-sm text-grey-7 mb-3')
        
        def export_csv() -> bytes:
            """CSVデータを生成"""
            # データフレームをコピーして、カラム名を変更
            df = dataset.data.copy()
            
            # 前処理内容に応じてカラム名を決定
            new_column_names = _get_export_column_names(x_col, y_col, preprocessing_options)
            
            # カラム名を変更（x_col, y_colが存在する場合のみ）
            rename_dict = {}
            if x_col in df.columns:
                rename_dict[x_col] = new_column_names['x']
            if y_col in df.columns:
                rename_dict[y_col] = new_column_names['y']
            
            if rename_dict:
                df = df.rename(columns=rename_dict)
            
            # BytesIOを使用してCSVデータを生成
            buffer = BytesIO()
            df.to_csv(buffer, index=False, encoding='utf-8-sig')
            buffer.seek(0)
            return buffer.getvalue()
        
        # ダウンロードボタン
        ui.button(
            '前処理後データをCSVでダウンロード',
            icon='download',
            on_click=lambda: ui.download(
                export_csv(),
                filename=f'{dataset.id}_processed.csv'
            )
        ).props('color=positive').classes('w-full')


def _get_export_column_names(
    x_col: str,
    y_col: str,
    preprocessing_options: PreprocessingOptions
) -> dict[str, str]:
    """エクスポート時のカラム名を決定
    
    Args:
        x_col: X軸のカラム名
        y_col: Y軸のカラム名
        preprocessing_options: 前処理オプション
        
    Returns:
        dict: 'x', 'y'のキーを持つ辞書（新しいカラム名）
    """
    convert_true = preprocessing_options.get('convert_true', False)
    convert_plastic = preprocessing_options.get('convert_plastic', False)
    
    # 塑性ひずみに変換した場合
    if convert_plastic:
        return {
            'x': 'plastic_strain',
            'y': 'true_stress'
        }
    
    # 真ひずみに変換した場合
    if convert_true:
        return {
            'x': 'true_strain',
            'y': 'true_stress'
        }
    
    # どちらも変換していない場合は元のカラム名を使用
    return {
        'x': x_col,
        'y': y_col
    }
