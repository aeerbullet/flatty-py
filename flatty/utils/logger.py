"""
flatty/utils/logger.py
统一日志配置。
"""
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    获取配置好的 logger 实例。
    如果根 logger 尚未配置，则进行初始化。
    """
    logger = logging.getLogger(name)
    
    # 如果已经配置过 handler，直接返回（避免重复添加）
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 创建控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 添加到 Logger
    logger.addHandler(console_handler)
    
    # 防止日志传播到根 logger (避免重复输出)
    logger.propagate = False

    return logger