"""installer.log - 日志系统

封装 stdlib logging，提供:
- 控制台 + 文件双输出
- RotatingFileHandler 自动滚动
- EXE 模式自动重定向到 %USERPROFILE%\\OneInstall\\logs\\
- 分级日志(DEBUG/INFO/WARN/ERROR)

按 CLAUDE.md §1.4 铁律: 失败必须 ERROR + 截图, 禁止 print 代替 logger.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 日志格式: 时间 [级别] 消息
LOG_FORMAT = "%(asctime)s [%(levelname)-5s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 文件滚动: 单文件 5MB, 保留 10 份
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 10

_logger_cache: dict[str, logging.Logger] = {}


def _resolve_log_dir(log_dir: str | None) -> Path:
    """解析日志目录.
    - 显式传参: 优先用
    - 运行环境是 EXE(SysFrozen): 用 %USERPROFILE%\\OneInstall\\logs\\
    - 否则: 用当前目录的 logs/
    """
    if log_dir:
        return Path(log_dir)

    if getattr(sys, "frozen", False):
        # 打包成 EXE 后
        user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        return Path(user_profile) / "OneInstall" / "logs"

    # 开发模式: 当前目录下的 logs/
    return Path.cwd() / "logs"


def setup_logging(
    name: str = "OneInstall",
    log_dir: str | None = None,
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
) -> logging.Logger:
    """初始化日志系统.

    Args:
        name: logger 名, 多次调用同名返回同一实例
        log_dir: 日志目录, None 时按 EXE/开发模式自动选择
        file_level: 文件日志级别, 默认 DEBUG
        console_level: 控制台日志级别, 默认 INFO

    Returns:
        配置好的 logger 实例
    """
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # logger 级别取最低, 由 handler 过滤
    logger.propagate = False  # 不往 root logger 传, 避免重复

    # 避免重复绑定 handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ---- 文件 handler ----
    resolved_dir = _resolve_log_dir(log_dir)
    try:
        resolved_dir.mkdir(parents=True, exist_ok=True)
        log_file = resolved_dir / f"install_{_today()}.log"
        fh = RotatingFileHandler(
            log_file,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        fh.setLevel(file_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except OSError as exc:
        # 目录创建失败也不能让程序挂掉, 降级到 stderr
        print(f"[WARN ] 日志文件初始化失败: {exc}", file=sys.stderr)

    # ---- 控制台 handler ----
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(console_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    _logger_cache[name] = logger
    logger.debug("日志系统初始化完成: name=%s, dir=%s", name, resolved_dir)
    return logger


def get_logger(name: str = "OneInstall") -> logging.Logger:
    """获取已初始化的 logger, 未初始化则兜底初始化."""
    if name in _logger_cache:
        return _logger_cache[name]
    return setup_logging(name=name)


def _today() -> str:
    """YYYYMMDD 格式今天日期, 避免引入 datetime 反复构造."""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")


def shutdown() -> None:
    """关闭所有 handler (打包 EXE 退出前调用, 防止日志丢失)."""
    for logger in _logger_cache.values():
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
    _logger_cache.clear()
