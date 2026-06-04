"""OneInstall - 一键自动安装器.

技术栈: Python 3.11+ / pywinauto / PyYAML / Pillow.
设计原则: 配置驱动 / 策略可替换 / 失败可观测 / 防御性编程.
"""
from .core import AutoInstaller, DEFAULT_EXE_PATH
from .log import get_logger, setup_logging
from .config import load_config
from .strategies import silent_install, gui_install

__all__ = [
    "AutoInstaller",
    "DEFAULT_EXE_PATH",
    "get_logger",
    "setup_logging",
    "load_config",
    "silent_install",
    "gui_install",
]

__version__ = "0.1.0"
