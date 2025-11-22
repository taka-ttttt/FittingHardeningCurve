"""カスタム例外定義"""


class FitCurveException(Exception):
    """FitCurveアプリケーションのベース例外"""
    pass


class DataValidationError(FitCurveException):
    """データバリデーションエラー
    
    データが不正、不足、または形式が不適切な場合に発生
    """
    pass


class FittingError(FitCurveException):
    """フィッティング実行エラー
    
    フィッティングアルゴリズムの実行中にエラーが発生した場合
    """
    pass


class DatasetNotFoundError(FitCurveException):
    """データセットが見つからないエラー
    
    指定されたIDのデータセットが存在しない場合
    """
    pass


class FileOperationError(FitCurveException):
    """ファイル操作エラー
    
    ファイルの読み書き中にエラーが発生した場合
    """
    pass


class ConfigurationError(FitCurveException):
    """設定エラー
    
    不正な設定値または設定の不整合がある場合
    """
    pass

