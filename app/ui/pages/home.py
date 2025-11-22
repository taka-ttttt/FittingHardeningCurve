"""ホームページ"""

from nicegui import ui

from app.ui.layout import create_card, navigate_to


def render() -> None:
    """ホームページをレンダリング"""
    
    with ui.column().classes('w-full max-w-6xl mx-auto p-6 gap-6'):
        # ヘッダー
        with ui.row().classes('items-center gap-4 mb-4'):
            ui.icon('science', size='48px').classes('text-primary')
            ui.label('FitCurve').classes('text-5xl font-bold text-primary')
        
        ui.label('カーブフィッティングWebアプリケーション').classes('text-xl text-grey-7 mb-6')
        
        # 機能紹介
        with create_card('主な機能', 'star'):
            with ui.grid(columns=3).classes('gap-4 w-full'):
                # データアップロードと前処理
                with ui.card().classes('p-4 hover:shadow-lg transition-shadow cursor-pointer').on('click', lambda: navigate_to('/upload')):
                    with ui.column().classes('items-center gap-3'):
                        ui.icon('upload', size='48px').classes('text-blue-500')
                        ui.label('データと前処理').classes('text-lg font-bold')
                        ui.label('アップロード・応力-ひずみ変換').classes('text-sm text-grey-6 text-center')
                
                # フィッティング
                with ui.card().classes('p-4 hover:shadow-lg transition-shadow cursor-pointer').on('click', lambda: navigate_to('/fit')):
                    with ui.column().classes('items-center gap-3'):
                        ui.icon('analytics', size='48px').classes('text-orange-500')
                        ui.label('フィッティング').classes('text-lg font-bold')
                        ui.label('モデルでフィット実行').classes('text-sm text-grey-6 text-center')
                
                # 結果管理
                with ui.card().classes('p-4 hover:shadow-lg transition-shadow cursor-pointer').on('click', lambda: navigate_to('/results')):
                    with ui.column().classes('items-center gap-3'):
                        ui.icon('folder', size='48px').classes('text-purple-500')
                        ui.label('結果管理').classes('text-lg font-bold')
                        ui.label('過去の結果を保存・再利用').classes('text-sm text-grey-6 text-center')
        
        # 対応モデル
        with create_card('対応フィッティングモデル', 'functions'):
            with ui.column().classes('gap-3'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('calculate', color='primary')
                    ui.label('多項式フィット').classes('font-bold')
                    ui.label('y = a₀ + a₁x + a₂x² + ...').classes('font-mono text-sm text-grey-7')
                
                with ui.row().classes('items-center gap-3'):
                    ui.icon('trending_up', color='primary')
                    ui.label('指数関数フィット').classes('font-bold')
                    ui.label('y = a·exp(bx) + c').classes('font-mono text-sm text-grey-7')
                
                with ui.row().classes('items-center gap-3'):
                    ui.icon('show_chart', color='primary')
                    ui.label('対数関数フィット').classes('font-bold')
                    ui.label('y = a + b·ln(x)').classes('font-mono text-sm text-grey-7')
                
                with ui.row().classes('items-center gap-3'):
                    ui.icon('query_stats', color='primary')
                    ui.label('べき乗関数フィット').classes('font-bold')
                    ui.label('y = a·xᵇ').classes('font-mono text-sm text-grey-7')
        
        # クイックスタート
        with create_card('クイックスタート', 'play_circle'):
            with ui.stepper().props('vertical').classes('w-full') as stepper:
                with ui.step('ステップ1: データアップロードと前処理'):
                    ui.label('CSVファイルをアップロードし、必要に応じて応力-ひずみデータの単位変換や塑性ひずみへの変換を行います').classes('mb-4')
                    with ui.stepper_navigation():
                        ui.button('次へ', on_click=stepper.next).props('flat')
                
                with ui.step('ステップ2: フィッティング'):
                    ui.label('フィットページでモデルを選択してパラメータを設定し、実行します').classes('mb-4')
                    with ui.stepper_navigation():
                        ui.button('次へ', on_click=stepper.next).props('flat')
                        ui.button('戻る', on_click=stepper.previous).props('flat')
                
                with ui.step('ステップ3: 結果確認とエクスポート'):
                    ui.label('フィット曲線、残差、統計指標を確認し、結果を画像やCSVで保存します').classes('mb-4')
                    with ui.stepper_navigation():
                        ui.button('完了', on_click=stepper.next).props('flat color=primary')
                        ui.button('戻る', on_click=stepper.previous).props('flat')
        
        # 始めるボタン
        with ui.row().classes('justify-center mt-8'):
            ui.button(
                '今すぐ始める',
                icon='arrow_forward',
                on_click=lambda: navigate_to('/upload')
            ).props('size=lg color=primary').classes('px-8 py-3 text-lg')

