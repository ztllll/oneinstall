"""installer.screenshot - 失败自动截图

按 CLAUDE.md §1.4 铁律: 失败必须截图, 路径回写日志.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

# 用 Pillow 做跨平台截图, 避免 Windows-only 依赖
try:
    from PIL import ImageGrab  # type: ignore
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


def _resolve_screenshot_dir(save_dir: str | None) -> Path:
    """解析截图目录, EXE 模式重定向到 %USERPROFILE%\\OneInstall\\screenshots\\."""
    if save_dir:
        return Path(save_dir)

    if getattr(sys, "frozen", False):
        user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        return Path(user_profile) / "OneInstall" / "screenshots"

    return Path.cwd() / "screenshots"


def save_screenshot(
    tag: str = "fail",
    save_dir: str | None = None,
) -> str | None:
    """截全屏并保存到文件.

    Args:
        tag: 文件名标记, e.g. "timeout" / "btn_not_found" / "exception"
        save_dir: 保存目录, None 时按 EXE/开发模式自动选择

    Returns:
        保存的文件绝对路径, 失败返回 None
    """
    if not _HAS_PIL:
        return None

    resolved_dir = _resolve_screenshot_dir(save_dir)
    try:
        resolved_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 文件名: screenshot_<tag>_<时间戳>.png
    safe_tag = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in tag)
    file_path = resolved_dir / f"screenshot_{safe_tag}_{ts}.png"

    try:
        # ImageGrab.grab() 在 Windows 上截全屏; Linux 上需要 X11
        img = ImageGrab.grab()
        img.save(str(file_path), format="PNG")
        return str(file_path.resolve())
    except Exception:
        # 截图失败不能抛, 静默返回 None, 调用方会判断
        return None


def save_window_screenshot(
    window_handle: int,
    tag: str = "window",
    save_dir: str | None = None,
) -> str | None:
    """截指定窗口(Windows 专属, 用 win32 API). 跨平台 fallback 到 save_screenshot.

    Args:
        window_handle: 窗口句柄(hwnd)
        tag: 文件名标记
        save_dir: 保存目录

    Returns:
        保存的文件绝对路径
    """
    if not _HAS_PIL:
        return None

    resolved_dir = _resolve_screenshot_dir(save_dir)
    try:
        resolved_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_tag = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in tag)
    file_path = resolved_dir / f"screenshot_{safe_tag}_{ts}.png"

    # Windows: 用 ImageGrab.grab(bbox=...) 截窗口区域
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            # 用 win32 API 取窗口尺寸
            GetWindowRect = ctypes.windll.user32.GetWindowRect
            GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
            GetWindowRect.restype = wintypes.BOOL

            rect = wintypes.RECT()
            if GetWindowRect(window_handle, ctypes.byref(rect)):
                bbox = (rect.left, rect.top, rect.right, rect.bottom)
                img = ImageGrab.grab(bbox=bbox)
                img.save(str(file_path), format="PNG")
                return str(file_path.resolve())
        except Exception:
            pass

    # fallback: 全屏截图
    return save_screenshot(tag=tag, save_dir=save_dir)
