"""installer.strategies - 安装策略

核心三层自适应 (CLAUDE.md §1.3):
  1. silent_install: 按顺序尝试静默参数
  2. gui_install: pywinauto GUI 自动化
  3. 失败兜底: 截图 + 错误返回
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .log import get_logger
from .screenshot import save_screenshot

# pywinauto 是 Windows-only, 跨平台开发要延迟 import
_PYWINAUTO_AVAILABLE: bool | None = None


def _check_pywinauto() -> bool:
    """检查 pywinauto 是否可用(Windows 平台)."""
    global _PYWINAUTO_AVAILABLE
    if _PYWINAUTO_AVAILABLE is not None:
        return _PYWINAUTO_AVAILABLE

    if sys.platform != "win32":
        _PYWINAUTO_AVAILABLE = False
        return False

    try:
        import pywinauto  # noqa: F401
        _PYWINAUTO_AVAILABLE = True
    except ImportError:
        _PYWINAUTO_AVAILABLE = False

    return _PYWINAUTO_AVAILABLE


# -------------------- 数据结构 --------------------

@dataclass
class SilentResult:
    """静默安装结果."""
    success: bool
    exit_code: int | None
    used_args: str | None
    error: str | None = None


@dataclass
class GuiResult:
    """GUI 安装结果."""
    success: bool
    clicked_count: int = 0
    error: str | None = None
    screenshot_path: str | None = None
    actions_log: list[str] = field(default_factory=list)


# -------------------- 策略 1: 静默安装 --------------------

def silent_install(
    exe_path: str,
    args_list: list[str],
    timeout_per_try: int = 120,
    process_runner: Callable[..., Any] | None = None,
) -> SilentResult:
    """按顺序尝试静默参数, 第一个成功的就用.

    Args:
        exe_path: 目标 exe 路径
        args_list: 静默参数列表(按优先级排序)
        timeout_per_try: 每个参数的超时(秒)
        process_runner: 注入的进程执行函数(测试用), 默认用 subprocess

    Returns:
        SilentResult
    """
    logger = get_logger()

    if process_runner is None:
        import subprocess
        def process_runner(args, timeout):
            return subprocess.run(
                args,
                capture_output=True,
                timeout=timeout,
            )

    for args in args_list:
        logger.info("尝试静默参数: %s", args)
        cmd = [exe_path] + args.split() if isinstance(args, str) else [exe_path] + list(args)
        try:
            proc = process_runner(cmd, timeout=timeout_per_try)
            exit_code = getattr(proc, "returncode", -1)
            # 成功判定: 退出码 0 或 3010(需重启)
            if exit_code in (0, 3010):
                logger.info("✓ 静默安装成功(退出码=%d, 参数=%s)", exit_code, args)
                return SilentResult(success=True, exit_code=exit_code, used_args=args)
            logger.warning("静默参数 %s 失败(退出码=%d)", args, exit_code)
        except Exception as exc:
            # TimeoutExpired / FileNotFoundError / OSError
            logger.warning("静默参数 %s 异常: %s", args, exc)

    logger.warning("所有静默参数均失败")
    return SilentResult(success=False, exit_code=None, used_args=None,
                        error="所有静默参数尝试均失败")


# -------------------- 策略 2: GUI 自动化 --------------------

def gui_install(
    exe_path: str,
    wizard_buttons: list[dict],
    timeout: int = 600,
    step_timeout: int = 30,
    skip_on_error: bool = True,
    debug_screenshot: bool = False,
    screenshot_dir: str | None = None,
) -> GuiResult:
    """GUI 模式自动安装.

    核心循环:
      1. 启动 exe
      2. 等待安装窗口出现(最多 step_timeout 秒)
      3. 在窗口中按 wizard_buttons 顺序匹配按钮并执行
      4. 第一个 is_done=True 的按钮被点击 → 视为完成
      5. 超过总 timeout → 失败, 截图退出

    Args:
        exe_path: 目标 exe 路径
        wizard_buttons: 按钮规则列表
        timeout: 总超时(秒)
        step_timeout: 单步超时(秒)
        skip_on_error: 按钮点击失败时是否继续
        debug_screenshot: 是否每步截图
        screenshot_dir: 截图目录

    Returns:
        GuiResult
    """
    logger = get_logger()

    if not _check_pywinauto():
        msg = "pywinauto 不可用(非 Windows 平台或未安装), 无法 GUI 自动化"
        logger.error(msg)
        return GuiResult(success=False, error=msg)

    # 延迟 import, 避免 Linux 上 import 报错
    from pywinauto import Application, timings

    # 加快轮询间隔, 默认 0.5s 我们改 0.3s
    timings.Timings.window_find_timeout = step_timeout

    actions_log: list[str] = []
    start_time = time.time()
    clicked_count = 0
    app = None

    try:
        logger.info("启动 exe: %s", exe_path)
        app = Application(backend="uia").start(exe_path)
    except Exception as exc:
        msg = f"启动 exe 失败: {exc}"
        logger.error(msg)
        return GuiResult(success=False, error=msg)

    try:
        # 主循环
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                path = save_screenshot("timeout", screenshot_dir)
                msg = f"总超时({timeout}s)退出"
                logger.error(msg)
                return GuiResult(
                    success=False,
                    clicked_count=clicked_count,
                    error=msg,
                    screenshot_path=path,
                    actions_log=actions_log,
                )

            # 找安装窗口
            window = _find_install_window(app, step_timeout)
            if window is None:
                logger.debug("等待安装窗口出现...")
                time.sleep(0.3)
                continue

            # 按顺序匹配按钮
            clicked_done = False
            for rule in wizard_buttons:
                try:
                    matched = _find_button_in_window(window, rule, step_timeout)
                    if matched is None:
                        continue

                    action = rule.get("action", "click")
                    is_done = rule.get("is_done", False)
                    name = rule.get("names", ["unknown"])[0]

                    if action == "check":
                        matched.check()
                        actions_log.append(f"check:{name}")
                        logger.info("✓ 勾选: %s", name)
                    elif action == "click":
                        matched.click()
                        actions_log.append(f"click:{name}")
                        logger.info("✓ 点击: %s", name)
                        clicked_count += 1

                        if is_done:
                            clicked_done = True
                            break

                    if debug_screenshot:
                        save_screenshot(f"step_{clicked_count}", screenshot_dir)

                except Exception as exc:
                    err_msg = f"按钮操作失败: {exc}"
                    if skip_on_error:
                        logger.warning("%s (已跳过)", err_msg)
                    else:
                        path = save_screenshot("btn_error", screenshot_dir)
                        logger.error("%s, 退出", err_msg)
                        return GuiResult(
                            success=False,
                            clicked_count=clicked_count,
                            error=err_msg,
                            screenshot_path=path,
                            actions_log=actions_log,
                        )

            if clicked_done:
                logger.info("✓ 安装完成, 共点击 %d 次", clicked_count)
                return GuiResult(
                    success=True,
                    clicked_count=clicked_count,
                    actions_log=actions_log,
                )

            # 这轮没找到任何按钮, 等一下再试
            time.sleep(0.3)

    except KeyboardInterrupt:
        path = save_screenshot("interrupted", screenshot_dir)
        msg = "用户中断 (Ctrl+C)"
        logger.error(msg)
        return GuiResult(success=False, clicked_count=clicked_count,
                         error=msg, screenshot_path=path, actions_log=actions_log)
    finally:
        # 清理 app 引用
        if app is not None:
            try:
                del app
            except Exception:
                pass


# -------------------- GUI 内部辅助 --------------------

def _find_install_window(app, timeout: int):
    """找到当前激活的安装窗口.

    策略:
      1. 优先找标题含 安装/Setup/Install 的窗口
      2. fallback 到第一个可见的顶层窗口
    """
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")

        # 策略1: 标题匹配
        title_patterns = ["安装", "Setup", "Install", "Installer", "Wizard"]
        deadline = time.time() + timeout
        while time.time() < deadline:
            for pattern in title_patterns:
                try:
                    windows = desktop.windows(title_re=f".*{pattern}.*", visible_only=True)
                    if windows:
                        return windows[0]
                except Exception:
                    continue
            time.sleep(0.2)

        # 策略2: 兜底 - 第一个可见顶层窗口
        try:
            all_windows = desktop.windows(visible_only=True)
            for w in all_windows:
                # 排除明显不是安装程序的窗口(资源管理器等)
                title = w.window_text()
                if title and title not in ("Program Manager", "Desktop"):
                    return w
        except Exception:
            pass

    except Exception as exc:
        get_logger().debug("找窗口异常: %s", exc)

    return None


def _find_button_in_window(window, rule: dict, timeout: int):
    """在窗口中按规则查找按钮, 多策略匹配.

    策略:
      1. 精确匹配 name + control_type
      2. 模糊匹配(contains)
      3. 模糊匹配(去除 & 快捷键前缀)
    """
    try:
        names = rule.get("names", [])
        control_type = rule.get("control_type", "Button")
        deadline = time.time() + timeout

        while time.time() < deadline:
            # 策略1: 精确匹配
            for name in names:
                try:
                    btn = window.child_window(title=name, control_type=control_type)
                    if btn.exists(timeout=0.1):
                        return btn
                except Exception:
                    continue

            # 策略2: 模糊匹配(取所有 Button/CheckBox, 检查文字包含 keywords)
            try:
                ctype_plural = "Buttons" if control_type == "Button" else "CheckBoxes"
                descendants = window.descendants(**{ctype_plural: True})
                for ctrl in descendants:
                    try:
                        text = ctrl.window_text()
                        if not text:
                            continue
                        # 去 & 快捷键前缀
                        normalized = text.replace("&", "")
                        for name in names:
                            if name in text or name.replace("&", "") in normalized:
                                return ctrl
                    except Exception:
                        continue
            except Exception:
                pass

            time.sleep(0.2)

    except Exception as exc:
        get_logger().debug("按钮匹配异常: %s", exc)

    return None
