"""パフォーマンス監視とロギングユーティリティ"""

import time
from functools import wraps
from typing import Any, Callable

from app.logging_conf import get_logger

logger = get_logger(__name__)


def performance_monitor(func: Callable) -> Callable:
    """関数の実行時間を監視するデコレータ
    
    使用例:
        @performance_monitor
        def slow_function():
            time.sleep(1)
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__qualname__}"
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # 実行時間に応じてログレベルを変更
            if elapsed > 5.0:
                logger.warning(f"⚠️  {func_name} took {elapsed:.2f}s (slow!)")
            elif elapsed > 1.0:
                logger.info(f"⏱️  {func_name} took {elapsed:.2f}s")
            else:
                logger.debug(f"✓ {func_name} took {elapsed:.3f}s")
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"❌ {func_name} failed after {elapsed:.2f}s: {e}",
                exc_info=True
            )
            raise
    
    return wrapper


def log_method_call(func: Callable) -> Callable:
    """メソッド呼び出しをログに記録するデコレータ
    
    使用例:
        @log_method_call
        def important_operation(param):
            pass
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = f"{func.__module__}.{func.__qualname__}"
        logger.debug(f"→ Calling {func_name}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"← {func_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"← {func_name} failed: {e}")
            raise
    
    return wrapper

