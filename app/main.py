"""FitCurve - メインエントリポイント"""

from nicegui import app, ui

from app.logging_conf import get_logger, setup_logging
from app.settings import settings
from app.ui import pages
from app.ui.layout import create_footer, create_header

# ログ設定
setup_logging()
logger = get_logger(__name__)


# ルーティング設定
@ui.page('/')
def index_page():
    """ホームページ"""
    create_header('/')
    pages.home.render()
    create_footer()


@ui.page('/upload')
def upload_page():
    """データアップロード・可視化ページ"""
    create_header('/upload')
    pages.upload.render()
    create_footer()


@ui.page('/fit')
def fit_page():
    """フィッティングページ"""
    create_header('/fit')
    pages.fit.render()
    create_footer()


@ui.page('/results')
def results_page():
    """結果管理ページ"""
    create_header('/results')
    pages.results.render()
    create_footer()


# 静的ファイル配信（データディレクトリ）
app.add_static_files('/data', str(settings.data_dir))


def main():
    """アプリケーション起動"""
    logger.info('FitCurve アプリケーションを起動します')
    logger.info(f'環境: {settings.app_env}')
    logger.info(f'ポート: {settings.app_port}')
    logger.info(f'ホスト: {settings.app_host}')
    
    ui.run(
        title='FitCurve - Curve Fitting Tool',
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        show=settings.debug,
        favicon='🔬'
    )


if __name__ in {'__main__', '__mp_main__'}:
    main()

