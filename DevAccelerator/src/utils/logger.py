"""
日志工具模块
"""
import logging
import logging.handlers
from pathlib import Path
from config.settings import LOGS_DIR, LOG_LEVEL, LOG_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT

def setup_logger(name: str, level: str = LOG_LEVEL) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式器
    formatter = logging.Formatter(LOG_FORMAT)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=LOG_MAX_SIZE, 
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 创建应用主日志记录器
app_logger = setup_logger("DevAccelerator")