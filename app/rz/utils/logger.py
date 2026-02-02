import logging
import sys
from typing import Optional
from app.core.config import settings


_INITIALIZED = False


def setup_global_logging(module_name: Optional[str] = None) -> logging.Logger:

    global _INITIALIZED
    
    # 只在第一次调用时初始化
    if not _INITIALIZED:
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        log_format = settings.LOG_FORMAT

        # log_file = getattr(settings, 'LOG_FILE', '/tmp/app.log')  # 设置默认日志文件路径
        
        # DEBUG 格式兜底
        if settings.LOG_LEVEL.upper() == "DEBUG" and not log_format:
            log_format = "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s"
        
        # 默认格式兜底
        if not log_format:
            log_format = "[%(asctime)s] %(levelname)s [%(name)s] %(message)s"
        
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        if not root_logger.handlers:
            # 独立脚本场景
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(log_level)
            handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(handler)
        else:
            # FastAPI/Uvicorn 场景
            formatter = logging.Formatter(log_format)
            for handler in root_logger.handlers:
                handler.setFormatter(formatter)
        
        _INITIALIZED = True
    
    # 自动检测模块名
    if module_name is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            module_name = frame.f_back.f_globals.get('__name__', 'root')
        else:
            module_name = 'root'
    
    return logging.getLogger(module_name)


# 全局 logger 实例
logger = setup_global_logging()


# from app.rz.utils.logger import setup_global_logging, logger

# # 使用全局logger实例
# logger.info("This is an info message")

# # 或者根据需要创建特定模块的logger实例
# module_logger = setup_global_logging(__name__)
# module_logger.info("This is an info message from module_logger")