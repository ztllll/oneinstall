"""OneInstall 主入口.

用法:
  python main.py                                    # 默认: M:\\考试资源\\安装\\1.exe
  python main.py --exe "D:\\app.exe"                # 指定 exe
  python main.py --config "nsis"                    # 指定配置
  python main.py --exe "X.exe" --config "innosetup" --timeout 300
"""
from __future__ import annotations

import argparse
import io
import os
import sys

# 强制 UTF-8 stdout/stderr, 避免 Windows cp1252/cp936 编码问题
# 必须在任何 print() 之前
if sys.stdout and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):
        pass
if sys.stderr and hasattr(sys.stderr, "buffer"):
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):
        pass

# 也设置环境变量, 给子进程用
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

from installer.config import list_configs
from installer.core import AutoInstaller, DEFAULT_EXE_PATH
from installer.log import get_logger, shutdown


def parse_args() -> argparse.Namespace:
    """解析命令行参数."""
    parser = argparse.ArgumentParser(
        prog="OneInstall",
        description="一键自动安装器 - 自适应多种 Windows 安装程序",
    )
    parser.add_argument(
        "--exe", "-e",
        default=DEFAULT_EXE_PATH,
        help=f"目标 exe 路径 (默认: {DEFAULT_EXE_PATH})",
    )
    parser.add_argument(
        "--config", "-c",
        default="default",
        help="配置名(对应 configs/<name>.yaml, 默认: default)",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=None,
        help="总超时秒数(覆盖配置文件, 默认 600)",
    )
    parser.add_argument(
        "--debug-screenshot",
        action="store_true",
        help="调试模式: 每步截图",
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="列出所有可用配置后退出",
    )
    return parser.parse_args()


def main() -> int:
    """主入口函数.

    Returns:
        进程退出码: 0 = 成功, 1 = 失败, 2 = 参数错误
    """
    args = parse_args()

    if args.list_configs:
        configs = list_configs()
        print("可用配置:")
        for c in configs:
            print(f"  - {c}")
        return 0

    logger = get_logger()
    logger.info("命令行参数: exe=%s, config=%s", args.exe, args.config)

    try:
        installer = AutoInstaller(
            exe_path=args.exe,
            config_name=args.config,
        )
    except ValueError as exc:
        logger.error("初始化失败: %s", exc)
        return 2

    # 命令行覆盖配置
    if args.timeout is not None:
        installer.config["timeout"] = args.timeout
    if args.debug_screenshot:
        installer.config["debug_screenshot"] = True

    # 执行安装
    success = installer.run()

    # 退出前确保日志 flush
    shutdown()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
