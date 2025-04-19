"""
日志配置模块

提供统一的日志配置，支持不同环境和级别的日志记录，
包括控制台输出和文件记录，支持格式化和过滤。
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Union
import traceback

from app.core.config import settings, API_ROOT

# 日志格式
DEFAULT_FORMAT = "%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)d)"
VERBOSE_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s - %(message)s (%(filename)s:%(lineno)d)"

# 日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# 日志路径
LOG_DIR = API_ROOT / "logs"
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志文件
LOG_FILE = LOG_DIR / "api.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"

# 日志配置参数
LOG_FILE_MAX_SIZE = getattr(settings, "LOG_FILE_MAX_SIZE", 10 * 1024 * 1024)  # 默认10MB
LOG_FILE_BACKUP_COUNT = getattr(settings, "LOG_FILE_BACKUP_COUNT", 5)          # 默认保留5个备份
ERROR_LOG_RETENTION_DAYS = getattr(settings, "ERROR_LOG_RETENTION_DAYS", 30)   # 默认保留30天

# 过滤器类 - 用于过滤特定模块的日志
class ModuleFilter(logging.Filter):
    """
    模块过滤器，只允许特定模块的日志通过
    
    Args:
        modules: 允许的模块名称列表
    """
    def __init__(self, modules: List[str]):
        super().__init__()
        self.modules = modules
        
    def filter(self, record: logging.LogRecord) -> bool:
        """检查日志记录是否来自允许的模块"""
        if not self.modules:
            return True
        return any(record.name.startswith(module) for module in self.modules)

# 异常跟踪格式化器
class ExceptionFormatter:
    """
    异常跟踪格式化器，提供更易读的异常跟踪格式
    """
    @staticmethod
    def format_exception(exc_info) -> str:
        """格式化异常信息为可读字符串"""
        if exc_info[0] is None:
            return ""
            
        exc_type, exc_value, exc_tb = exc_info
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        return "".join(tb_lines)

def get_log_level() -> int:
    """从配置获取日志级别"""
    level_name = settings.LOGGING_LEVEL.lower()
    return LOG_LEVELS.get(level_name, logging.INFO)

def configure_logging() -> None:
    """配置日志系统
    
    设置全局日志记录器，包括控制台和文件处理器
    """
    log_level = get_log_level()
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 移除已有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(DEFAULT_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 非测试环境添加文件处理器
    if not settings.TESTING:
        # 常规日志 - 按大小轮转
        file_handler = RotatingFileHandler(
            LOG_FILE, 
            maxBytes=LOG_FILE_MAX_SIZE,
            backupCount=LOG_FILE_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(VERBOSE_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # 错误日志 - 按日期轮转
        error_handler = TimedRotatingFileHandler(
            ERROR_LOG_FILE,
            when="midnight",
            interval=1,
            backupCount=ERROR_LOG_RETENTION_DAYS,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(VERBOSE_FORMAT)
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if settings.DEBUG else logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # 记录启动日志
    logging.info(f"日志系统已初始化 (级别: {logging.getLevelName(log_level)})")
    logging.info(f"环境: {settings.ENVIRONMENT}, 调试模式: {settings.DEBUG}, 测试模式: {settings.TESTING}")
    if not settings.TESTING:
        logging.info(f"日志文件路径: {LOG_FILE} (大小: {LOG_FILE_MAX_SIZE/1024/1024:.2f}MB, 保留: {LOG_FILE_BACKUP_COUNT}个)")
        logging.info(f"错误日志路径: {ERROR_LOG_FILE} (保留: {ERROR_LOG_RETENTION_DAYS}天)")

def get_logger(name: str) -> logging.Logger:
    """获取模块专用日志记录器
    
    Args:
        name: 模块名称，通常使用 __name__
        
    Returns:
        模块专用的日志记录器
    """
    logger = logging.getLogger(name)
    return logger 