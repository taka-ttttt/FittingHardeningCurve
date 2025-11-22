"""ファイル管理テーブルコンポーネント"""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from nicegui import ui


def create_data_preview_table(
    df: pd.DataFrame,
    max_rows: int = 10
) -> None:
    """データプレビューテーブルを作成
    
    Args:
        df: データフレーム
        max_rows: 表示最大行数
    """
    if df.empty:
        ui.label('データがありません').classes('text-grey-6 italic')
        return
    
    # 表示用にデータを制限
    display_df = df.head(max_rows)
    
    # テーブル用のデータを準備
    columns = [
        {'name': col, 'label': col, 'field': col, 'align': 'left'}
        for col in display_df.columns
    ]
    
    rows = display_df.to_dict('records')
    
    # テーブルを作成
    table = ui.table(
        columns=columns,
        rows=rows,
        row_key='index'
    ).classes('w-full')
    
    # 省略された行数を表示
    if len(df) > max_rows:
        ui.label(f'... 他 {len(df) - max_rows} 行').classes('text-sm text-grey-6 mt-2')


def create_dataset_info_card(
    filename: str,
    n_rows: int,
    n_cols: int,
    columns: list[str],
    file_size: int | None = None,
    upload_time: datetime | None = None
) -> None:
    """データセット情報カードを作成
    
    Args:
        filename: ファイル名
        n_rows: 行数
        n_cols: 列数
        columns: 列名リスト
        file_size: ファイルサイズ（バイト）
        upload_time: アップロード時刻
    """
    with ui.card().classes('w-full p-4'):
        with ui.row().classes('items-center gap-2 mb-3'):
            ui.icon('insert_drive_file', size='24px').classes('text-primary')
            ui.label(filename).classes('text-lg font-bold')
        
        with ui.column().classes('gap-2'):
            with ui.row().classes('gap-4'):
                ui.label(f'📊 {n_rows} 行 × {n_cols} 列')
                
                if file_size:
                    size_kb = file_size / 1024
                    ui.label(f'📁 {size_kb:.1f} KB')
                
                if upload_time:
                    ui.label(f'🕒 {upload_time.strftime("%Y/%m/%d %H:%M")}')
            
            ui.separator()
            
            ui.label('列:').classes('text-sm font-bold text-grey-7')
            with ui.row().classes('gap-2 flex-wrap'):
                for col in columns:
                    ui.chip(col, icon='label').props('size=sm')


def create_column_selector(
    columns: list[str],
    x_column: str | None = None,
    y_column: str | None = None,
    on_change: Callable[[str, str], None] | None = None
) -> dict[str, Any]:
    """列選択UIを作成
    
    Args:
        columns: 列名リスト
        x_column: デフォルトX列
        y_column: デフォルトY列
        on_change: 変更時のコールバック
        
    Returns:
        dict: {'x_select': Select, 'y_select': Select}
    """
    if not columns:
        ui.label('列が見つかりません').classes('text-warning')
        return {}
    
    x_default = x_column or columns[0]
    y_default = y_column or (columns[1] if len(columns) > 1 else columns[0])
    
    with ui.row().classes('gap-4 items-center'):
        ui.label('X軸:').classes('font-bold')
        x_select = ui.select(
            columns,
            value=x_default,
            label='X列を選択'
        ).classes('w-48')
        
        ui.label('Y軸:').classes('font-bold')
        y_select = ui.select(
            columns,
            value=y_default,
            label='Y列を選択'
        ).classes('w-48')
    
    if on_change:
        def handle_change():
            on_change(x_select.value, y_select.value)
        
        x_select.on_value_change(lambda: handle_change())
        y_select.on_value_change(lambda: handle_change())
    
    return {
        'x_select': x_select,
        'y_select': y_select
    }


def create_file_list(
    files: list[Path],
    on_select: Callable[[Path], None] | None = None,
    on_delete: Callable[[Path], None] | None = None
) -> None:
    """ファイルリストを作成
    
    Args:
        files: ファイルパスのリスト
        on_select: 選択時のコールバック
        on_delete: 削除時のコールバック
    """
    if not files:
        ui.label('ファイルがありません').classes('text-grey-6 italic')
        return
    
    for file_path in files:
        with ui.card().classes('w-full p-3 cursor-pointer hover:bg-grey-1').on('click', lambda f=file_path: on_select(f) if on_select else None):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('insert_drive_file', size='32px').classes('text-primary')
                    
                    with ui.column().classes('gap-1'):
                        ui.label(file_path.name).classes('font-bold')
                        
                        stat = file_path.stat()
                        size_kb = stat.st_size / 1024
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        
                        ui.label(f'{size_kb:.1f} KB | {mtime.strftime("%Y/%m/%d %H:%M")}').classes('text-sm text-grey-6')
                
                if on_delete:
                    ui.button(
                        icon='delete',
                        on_click=lambda f=file_path: on_delete(f)
                    ).props('flat round color=negative').classes('ml-auto')

