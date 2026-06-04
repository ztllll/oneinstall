"""installer.core - AutoInstaller 主类

编排整个安装流程 (CLAUDE.md §1.3):
  1. 文件校验
  2. 静默安装 (strategies.silent_install)
  3. 失败降级到 GUI (strategies.gui_install)
  4. 失败截图 + 错误返回
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from .config import load_config, validate_config
from .log import get_logger, setup_logging
from .screenshot import save_screenshot
from .strategies import (
    GuiResult,
    SilentResult,
    _check_pywinauto,
    gui_install,
    silent_install,
)

DEFAULT_EXE_PATH = r"M:\考试资源\安装\1.exe"


class AutoInstaller:
    """一键安装器主类."""

    def __init__(
        self,
        exe_path: str = DEFAULT_EXE_PATH,
        config: dict[str, Any] | None = None,
        config_name: str = "default",
    ):
        """初始化.

        Args:
            exe_path: 目标 exe 路径
            config: 直接传入配置 dict(优先于 config_name)
            config_name: 配置文件名(从 configs/<name>.yaml 加载)
        """
        # logger 必须先初始化, 后续所有日志都依赖它
        self.logger = setup_logging()

        self.exe_path = os.path.abspath(exe_path)

        if config is not None:
            self.config = config
        else:
            self.config = load_config(config_name)

        ok, err = validate_config(self.config)
        if not ok:
            self.logger.error("配置校验失败: %s", err)
            raise ValueError(f"配置校验失败: {err}")

    def run(self) -> bool:
        """执行完整安装流程.

        Returns:
            True = 安装成功, False = 失败
        """
        self.logger.info("=" * 60)
        self.logger.info("OneInstall 启动")
        self.logger.info("目标 exe: %s", self.exe_path)
        self.logger.info("=" * 60)

        # 1. 文件校验
        if not self._validate_exe():
            return False

        # 2. 策略1: 静默安装
        self.logger.info("[阶段 1/2] 尝试静默安装")
        silent_result = self._try_silent()

        if silent_result.success:
            self.logger.info("✓ 安装成功 (静默模式)")
            return True

        self.logger.warning("静默安装失败, 进入 GUI 模式")

        # 3. 策略2: GUI 自动化
        self.logger.info("[阶段 2/2] 启动 GUI 自动化")
        gui_result = self._try_gui()

        if gui_result.success:
            self.logger.info("✓ 安装成功 (GUI 模式, 共点击 %d 次)",
                             gui_result.clicked_count)
            return True

        # 4. 失败兜底
        self.logger.error("✗ 安装失败")
        self.logger.error("错误: %s", gui_result.error or "未知")
        if gui_result.screenshot_path:
            self.logger.error("失败截图: %s", gui_result.screenshot_path)

        return False

    # -------------------- 内部方法 --------------------

    def _validate_exe(self) -> bool:
        """校验 exe 文件存在且可执行."""
        path = Path(self.exe_path)
        if not path.exists():
            self.logger.error("文件不存在: %s", self.exe_path)
            return False
        if not path.is_file():
            self.logger.error("不是文件: %s", self.exe_path)
            return False
        if path.stat().st_size == 0:
            self.logger.error("文件大小为 0: %s", self.exe_path)
            return False

        size_mb = path.stat().st_size / (1024 * 1024)
        self.logger.info("文件存在, 大小: %.2f MB", size_mb)
        return True

    def _try_silent(self) -> SilentResult:
        """尝试静默安装."""
        return silent_install(
            exe_path=self.exe_path,
            args_list=self.config.get("silent_args", []),
            timeout_per_try=min(self.config.get("timeout", 600) // 3, 300),
        )

    def _try_gui(self) -> GuiResult:
        """尝试 GUI 自动化."""
        if not _check_pywinauto():
            return GuiResult(
                success=False,
                error="GUI 模式需要 Windows + pywinauto, 当前环境不可用",
            )

        return gui_install(
            exe_path=self.exe_path,
            wizard_buttons=self.config.get("wizard_buttons", []),
            timeout=self.config.get("timeout", 600),
            step_timeout=self.config.get("step_timeout", 30),
            skip_on_error=self.config.get("skip_on_error", True),
            debug_screenshot=self.config.get("debug_screenshot", False),
            screenshot_dir=self.config.get("screenshot_dir"),
        )
