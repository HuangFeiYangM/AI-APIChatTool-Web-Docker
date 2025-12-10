# app/utils/logger.py

_initialized = False
"""
日志配置模块
提供统一的日志配置和管理
"""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from app.config import settings


class CustomFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[94m',     # 蓝色
        'INFO': '\033[92m',      # 绿色
        'WARNING': '\033[93m',   # 黄色
        'ERROR': '\033[91m',     # 红色
        'CRITICAL': '\033[95m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    def format(self, record):
        """格式化日志记录"""
        # 添加颜色
        if settings.DEBUG and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
            record.name = f"{color}{record.name}{reset}"
        
        return super().format(record)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    设置日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为None则使用默认路径
        enable_console: 是否启用控制台输出
    """
    global _initialized
    if _initialized:
        return  # 已经初始化过，直接返回
    
    _initialized = True
    
    
    # 确定日志级别
    if log_level is None:
        log_level = settings.LOG_LEVEL
    
    # 设置默认日志文件路径（项目根目录的logs文件夹）
    if log_file is None:
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent  # app/utils/../../
        log_file = project_root / "logs" / "app.log"
    
    # 确保日志目录存在
    if log_file:
        log_path = Path(log_file).parent
        log_path.mkdir(parents=True, exist_ok=True)
        log_file_str = str(log_file)
    else:
        log_file_str = None
    
    # 日志配置字典
    log_config: Dict[str, Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': settings.LOG_FORMAT,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'colored': {
                '()': CustomFormatter,
                'format': settings.LOG_FORMAT,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'colored' if settings.DEBUG else 'default',
                'stream': sys.stdout
            }
        },
        'loggers': {
            '': {  # 根日志器
                'handlers': ['console'],
                'level': log_level,
                'propagate': True
            },
            'app': {  # 应用日志器
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'sqlalchemy.engine': {  # SQLAlchemy日志器
                'handlers': ['console'],
                'level': 'WARNING',  # 设置为WARNING减少日志噪音
                'propagate': False
            },
            'uvicorn': {  # Uvicorn日志器
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    
    # 添加文件处理器
    if log_file_str:
        log_config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'detailed',
            'filename': log_file_str,
            'maxBytes': 10 * 1024 * 1024,  # 10MB，可以根据需要调整
            'backupCount': 5,               # 保留5个备份文件
            'encoding': 'utf-8'
        }
        # 将文件处理器添加到日志器
        for logger_name in ['', 'app']:
            log_config['loggers'][logger_name]['handlers'].append('file')
    
    # 禁用控制台输出
    if not enable_console:
        for logger_config in log_config['loggers'].values():
            if 'console' in logger_config['handlers']:
                logger_config['handlers'].remove('console')
    
    # 应用配置
    logging.config.dictConfig(log_config)
    
    # 获取根日志器测试
    root_logger = logging.getLogger()
    root_logger.info(f"✅ 日志系统初始化完成 (级别: {log_level})")
    
    if log_file_str:
        root_logger.info(f"📁 日志文件: {log_file_str}")


def get_logger(name: str = "app") -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称，通常使用模块名
    
    Returns:
        配置好的日志器实例
    """
    return logging.getLogger(name)


# 全局日志级别映射
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def set_log_level(level: str) -> None:
    """
    动态设置日志级别
    
    Args:
        level: 日志级别字符串
    """
    if level.upper() not in LOG_LEVELS:
        raise ValueError(f"无效的日志级别: {level}")
    
    numeric_level = LOG_LEVELS[level.upper()]
    
    # 更新所有日志器
    for name, logger in logging.root.manager.loggerDict.items():
        if isinstance(logger, logging.Logger):
            logger.setLevel(numeric_level)
    
    logging.getLogger().info(f"日志级别已更新为: {level}")


# 导出常用函数
__all__ = [
    'setup_logging',
    'get_logger',
    'set_log_level',
    'CustomFormatter'
]

# 默认初始化（当模块被导入时）
if __name__ != "__main__":
    # 在非主模块中自动初始化
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_file=None,  # 使用默认路径：项目根目录/logs/app.log
        enable_console=True
    )
