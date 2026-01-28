import logging
from app.core.config import settings

def setup_global_logging(module_name: str = __name__) -> logging.Logger:
    # 配置根日志记录器
    log_level = settings.LOG_LEVEL
    log_format = settings.LOG_FORMAT

    if log_level == 'DEBUG':
        log_format =  '[%(asctime)s] - %(levelname)s - %(name)s - %(message)s'
        
    # log_file = getattr(settings, 'LOG_FILE', '/tmp/app.log')  # 设置默认日志文件路径

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            # logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # 创建并返回应用级别的日志记录器
    logger = logging.getLogger(module_name)
    return logger

# 创建全局logger实例
logger = setup_global_logging()


# from app.rz.utils.logger import setup_global_logging, logger

# # 使用全局logger实例
# logger.info("This is an info message")

# # 或者根据需要创建特定模块的logger实例
# module_logger = setup_global_logging(__name__)
# module_logger.info("This is an info message from module_logger")