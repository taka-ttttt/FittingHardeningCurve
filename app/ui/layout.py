"""共通レイアウトコンポーネント"""

from contextlib import contextmanager

from nicegui import ui


# ナビゲーションメニュー項目
MENU_ITEMS = [
    {'path': '/', 'label': 'ホーム', 'icon': 'home'},
    {'path': '/upload', 'label': 'データと前処理', 'icon': 'upload'},
    {'path': '/fit', 'label': 'フィッティング', 'icon': 'analytics'},
    {'path': '/results', 'label': '結果管理', 'icon': 'folder'},
]


def create_drawer(current_path: str = '/') -> ui.drawer:
    """サイドバー（ドロワー）を作成
    
    Args:
        current_path: 現在のパス
        
    Returns:
        ui.drawer: ドロワーオブジェクト
    """
    with ui.left_drawer(value=True, fixed=True, top_corner=True, bottom_corner=True).classes('bg-grey-1') as drawer:
        with ui.column().classes('w-full gap-2 p-4'):
            # ロゴ
            # with ui.row().classes('items-center gap-3 mb-4'):
            #     ui.icon('science', size='32px').classes('text-primary')
            #     ui.label('FittingHardeningCurve').classes('text-xl font-bold')
            
            # ui.separator()
            
            # ナビゲーションメニュー
            for item in MENU_ITEMS:
                create_nav_item(item['path'], item['label'], item['icon'], drawer, current_path)
                
    return drawer


def create_nav_item(path: str, label: str, icon: str, drawer: ui.drawer, current_path: str) -> None:
    """ナビゲーションアイテムを作成
    
    Args:
        path: パス
        label: ラベル
        icon: アイコン名
        drawer: ドロワーオブジェクト
        current_path: 現在のパス
    """
    is_active = current_path == path
    
    with ui.row().classes(
        f'w-full items-center gap-3 p-3 rounded cursor-pointer hover:bg-blue-50 '
        f'{"bg-blue-100" if is_active else ""}'
    ).on('click', lambda p=path: ui.navigate.to(p)):
    
        ui.icon(icon, size='24px').classes('text-primary' if is_active else '')
        ui.label(label).classes('font-bold' if is_active else '')


def navigate_to(path: str) -> None:
    """ページに遷移
    
    Args:
        path: 遷移先のパス
    """
    ui.navigate.to(path)


def create_header_button(path: str, label: str, icon: str) -> None:
    """ヘッダーボタンを作成
    
    Args:
        path: パス
        label: ラベル
        icon: アイコン名
    """
    ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(path)).props('flat').classes('text-white')


def create_header(current_path: str = '/') -> None:
    """ヘッダーを作成
    
    Args:
        current_path: 現在のパス
        
    Returns:
        ui.drawer: ドロワーオブジェクト（他のページから制御できるように返す）
    """
    drawer = create_drawer(current_path)
    
    with ui.header().classes('bg-primary text-white shadow-lg'):
        with ui.row().classes('w-full items-center justify-between px-4'):
            with ui.row().classes('items-center gap-4'):
                # ハンバーガーメニューボタン
                ui.button(icon='menu', on_click=drawer.toggle).props('flat round').classes('text-white')
                
                ui.icon('science', size='32px')
                ui.label('FittingHardeningCurve').classes('text-2xl font-bold')
            
            # デスクトップ用メニュー（オプション）
            # with ui.row().classes('gap-2 lg:flex'):
            #     for item in MENU_ITEMS:
            #         create_header_button(item['path'], item['label'], item['icon'])


def create_footer() -> None:
    """フッターを作成"""
    with ui.footer().classes('bg-grey-2 text-grey-7 py-4'):
        with ui.row().classes('w-full items-center justify-center gap-4'):
            ui.label('FittingHardeningCurve v0.1.0')
            ui.label('|')
            ui.link('GitHub', 'https://github.com/taka-ttttt/FittingHardeningCurve', new_tab=True)


@contextmanager
def create_page_container(title: str | None = None):
    """ページコンテナを作成
    
    Args:
        title: ページタイトル
    """
    with ui.column().classes('w-full max-w-7xl mx-auto p-4 gap-4'):
        if title:
            ui.label(title).classes('text-3xl font-bold text-primary')
        yield


@contextmanager
def create_card(title: str | None = None, icon: str | None = None):
    """カードコンテナを作成
    
    Args:
        title: カードタイトル
        icon: アイコン名
    """
    with ui.card().classes('w-full p-4'):
        if title:
            with ui.row().classes('items-center gap-2 mb-4'):
                if icon:
                    ui.icon(icon, size='24px').classes('text-primary')
                ui.label(title).classes('text-xl font-bold')
        yield


def show_notification(
    message: str,
    type: str = 'info',
    position: str = 'top-right',
    timeout: int = 3000
) -> None:
    """通知を表示
    
    Args:
        message: メッセージ
        type: タイプ（positive, negative, warning, info）
        position: 位置
        timeout: タイムアウト（ミリ秒）
    """
    ui.notify(
        message,
        type=type,
        position=position,
        timeout=timeout
    )


def create_loading_spinner(message: str = '処理中...'):
    """ローディングスピナーを作成
    
    Args:
        message: メッセージ
    """
    with ui.dialog() as dialog, ui.card():
        with ui.column().classes('items-center gap-4 p-4'):
            ui.spinner(size='lg')
            ui.label(message).classes('text-lg')
    
    return dialog

