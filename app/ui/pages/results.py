"""結果管理ページ"""

import json
from pathlib import Path

from nicegui import ui

from app.core.models.fit_result import FitResult
from app.core.services.exports import ExportService
from app.settings import settings
from app.ui.components.charts import (
    create_fit_plot,
    create_parameters_table,
    create_residual_plot,
    create_statistics_card,
)
from app.ui.layout import create_card, navigate_to, show_notification
from app.core.utils.fileio import list_files_by_pattern

# サービス
export_service = ExportService(settings.fits_dir)


def render() -> None:
    """結果ページをレンダリング"""
    
    with ui.column().classes('w-full max-w-6xl mx-auto p-6 gap-6'):
        ui.label('結果管理').classes('text-3xl font-bold text-primary mb-2')
        ui.label('過去のフィッティング結果を確認・管理します').classes('text-grey-7 mb-4')
        
        # 結果ファイルを取得
        result_files = list_files_by_pattern(
            settings.fits_dir,
            pattern='*_result.json',
            sort_by_mtime=True
        )
        
        if not result_files:
            with create_card('結果がありません', 'info'):
                ui.label('まだフィッティング結果がありません').classes('text-lg mb-4')
                ui.button(
                    'フィッティングを実行',
                    icon='analytics',
                    on_click=lambda: navigate_to('/fit')
                ).props('color=primary')
            return
        
        # 結果一覧
        with create_card('保存済み結果', 'folder'):
            ui.label(f'{len(result_files)} 件の結果').classes('text-sm text-grey-7 mb-4')
            
            results_list_container = ui.column().classes('w-full gap-3')
            detail_container = ui.column().classes('w-full gap-4')
            
            def load_result(filepath: Path) -> FitResult | None:
                """結果ファイルを読み込む"""
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return FitResult(**data)
                except Exception as e:
                    show_notification(f'読み込みエラー: {str(e)}', type='negative')
                    return None
            
            def display_result_list():
                """結果一覧を表示"""
                results_list_container.clear()
                
                with results_list_container:
                    for filepath in result_files:
                        result = load_result(filepath)
                        if result is None:
                            continue
                        
                        with ui.card().classes('w-full p-4 cursor-pointer hover:bg-grey-1').on('click', lambda r=result, f=filepath: show_result_detail(r, f)):
                            with ui.row().classes('w-full items-start justify-between'):
                                with ui.column().classes('gap-2 flex-grow'):
                                    # タイトル
                                    title = result.name or f'結果 {result.id[:8]}'
                                    ui.label(title).classes('text-lg font-bold')
                                    
                                    # 情報
                                    with ui.row().classes('gap-4 text-sm text-grey-6'):
                                        ui.label(f'📅 {result.created_at.strftime("%Y/%m/%d %H:%M")}')
                                        ui.label(f'📊 {result.config.method}')
                                        ui.label(f'📈 R²={result.statistics.r_squared:.4f}')
                                    
                                    # 関数式
                                    ui.label(result.get_fit_function_str()).classes('text-sm font-mono bg-grey-2 p-2 rounded mt-2')
                                
                                # アクション
                                with ui.column().classes('gap-2'):
                                    ui.button(
                                        icon='visibility',
                                        on_click=lambda r=result, f=filepath: show_result_detail(r, f)
                                    ).props('flat round color=primary')
                                    
                                    ui.button(
                                        icon='delete',
                                        on_click=lambda f=filepath: delete_result(f)
                                    ).props('flat round color=negative')
            
            def show_result_detail(result: FitResult, filepath: Path):
                """結果の詳細を表示"""
                detail_container.clear()
                
                with detail_container:
                    # 戻るボタン
                    with ui.row().classes('gap-2 mb-4'):
                        ui.button(
                            '一覧に戻る',
                            icon='arrow_back',
                            on_click=lambda: detail_container.clear()
                        ).props('flat')
                    
                    # 基本情報
                    with create_card('結果情報', 'info'):
                        with ui.column().classes('gap-2'):
                            ui.label(f'名前: {result.name or "N/A"}').classes('text-lg')
                            if result.description:
                                ui.label(f'説明: {result.description}')
                            ui.label(f'ID: {result.id}').classes('text-sm text-grey-6')
                            ui.label(f'作成日時: {result.created_at.strftime("%Y/%m/%d %H:%M:%S")}')
                            ui.label(f'手法: {result.config.method}')
                    
                    # フィットプロット
                    with create_card('フィット曲線', 'analytics'):
                        create_fit_plot(result)
                    
                    # パラメータ
                    create_parameters_table(result)
                    
                    # 統計指標
                    create_statistics_card(result)
                    
                    # 残差プロット
                    with create_card('残差分析', 'show_chart'):
                        with ui.tabs().classes('w-full') as tabs:
                            scatter_tab = ui.tab('散布図')
                            hist_tab = ui.tab('ヒストグラム')
                        
                        with ui.tab_panels(tabs, value=scatter_tab).classes('w-full'):
                            with ui.tab_panel(scatter_tab):
                                create_residual_plot(result, plot_type='scatter')
                            
                            with ui.tab_panel(hist_tab):
                                create_residual_plot(result, plot_type='histogram')
                    
                    # エクスポートオプション
                    with create_card('エクスポート', 'download'):
                        with ui.row().classes('gap-4 flex-wrap'):
                            ui.button(
                                'CSVダウンロード',
                                icon='file_download',
                                on_click=lambda: export_csv(result)
                            ).props('color=primary')
                            
                            ui.button(
                                'パラメータCSV',
                                icon='file_download',
                                on_click=lambda: export_parameters(result)
                            ).props('color=secondary')
                            
                            ui.button(
                                'レポート作成',
                                icon='description',
                                on_click=lambda: export_report(result)
                            ).props('color=positive')
            
            def delete_result(filepath: Path):
                """結果を削除"""
                try:
                    filepath.unlink()
                    
                    # 関連ファイルも削除
                    result_id = filepath.stem.replace('_result', '')
                    for pattern in [f'{result_id}_data.csv', f'{result_id}_parameters.csv']:
                        related_file = filepath.parent / pattern
                        if related_file.exists():
                            related_file.unlink()
                    
                    show_notification('結果を削除しました', type='positive')
                    
                    # 再読み込み
                    ui.navigate.reload()
                    
                except Exception as e:
                    show_notification(f'削除エラー: {str(e)}', type='negative')
            
            def export_csv(result: FitResult):
                """CSVエクスポート"""
                try:
                    # 一時ファイルに保存してダウンロード
                    csv_path = export_service.export_result_csv(result)
                    filename = f"{result.name or result.id[:8]}_data.csv"
                    
                    # ブラウザダウンロード
                    ui.download(src=str(csv_path), filename=filename)
                    show_notification('CSVをダウンロードします', type='positive')
                except Exception as e:
                    show_notification(f'エクスポートエラー: {str(e)}', type='negative')
            
            def export_parameters(result: FitResult):
                """パラメータCSVエクスポート"""
                try:
                    # 一時ファイルに保存してダウンロード
                    csv_path = export_service.export_parameters_csv(result)
                    filename = f"{result.name or result.id[:8]}_parameters.csv"
                    
                    # ブラウザダウンロード
                    ui.download(src=str(csv_path), filename=filename)
                    show_notification('パラメータCSVをダウンロードします', type='positive')
                except Exception as e:
                    show_notification(f'エクスポートエラー: {str(e)}', type='negative')
            
            def export_report(result: FitResult):
                """レポートエクスポート"""
                try:
                    # 一時ファイルに保存してダウンロード
                    report_path = export_service.create_summary_report(result)
                    filename = f"{result.name or result.id[:8]}_report.txt"
                    
                    # ブラウザダウンロード
                    ui.download(src=str(report_path), filename=filename)
                    show_notification('レポートをダウンロードします', type='positive')
                except Exception as e:
                    show_notification(f'エクスポートエラー: {str(e)}', type='negative')
            
            # 初期表示
            display_result_list()

