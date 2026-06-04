"""OneInstall 打包脚本.

用法:
  python build.py --nuitka         # 优先 Nuitka (体积小, 启动快)
  python build.py --pyinstaller    # Fallback PyInstaller (生态成熟)
  python build.py --nuitka --onefile  # Nuitka 强制单文件
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OneInstall 打包脚本")
    tool = parser.add_mutually_exclusive_group()
    tool.add_argument("--nuitka", action="store_true", help="用 Nuitka 打包(首选)")
    tool.add_argument("--pyinstaller", action="store_true", help="用 PyInstaller 打包(fallback)")
    parser.add_argument("--onefile", action="store_true", default=True, help="打成单文件(默认)")
    parser.add_argument("--no-console", action="store_true", default=True, help="不弹黑窗(默认)")
    parser.add_argument("--clean", action="store_true", help="先清空 build/dist")
    return parser.parse_args()


def check_platform() -> None:
    """Nuitka 编译需要 Windows 编译器."""
    if sys.platform != "win32":
        print("[WARN ] 当前平台非 Windows, 打包后可能无法在其他平台运行")
        print(f"        平台: {sys.platform}")


def clean() -> None:
    """清空 build/dist."""
    project_root = Path(__file__).resolve().parent
    for sub in ("build", "dist", "installer.build", "installer.dist",
                "installer.onefile-build", "__pycache__"):
        path = project_root / sub
        if path.exists():
            print(f"[CLEAN] 清理 {path}")
            shutil.rmtree(path, ignore_errors=True)


def build_with_nuitka(args: argparse.Namespace) -> int:
    """Nuitka 打包."""
    project_root = Path(__file__).resolve().parent

    cmd = [
        sys.executable, "-m", "nuitka",
        str(project_root / "main.py"),
        "--output-filename=OneInstall.exe",
        "--output-dir=dist",
        "--enable-plugin=anti-bloat",
        "--include-package=pywinauto",
        "--include-package=pywin32",
        "--include-package=PIL",
        "--include-data-dir=configs=configs",
        "--company-name=OneInstall",
        "--product-name=OneInstall",
        "--file-version=0.1.0",
        "--product-version=0.1.0",
    ]

    if args.onefile:
        cmd.append("--onefile")
    if args.no_console:
        cmd.append("--windows-disable-console")

    print(f"[BUILD] Nuitka 命令: {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=project_root)


def build_with_pyinstaller(args: argparse.Namespace) -> int:
    """PyInstaller 打包."""
    project_root = Path(__file__).resolve().parent

    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(project_root / "main.py"),
        "--name=OneInstall",
        "--distpath=dist",
        "--workpath=build",
        "--clean",
        "--noconfirm",
        # 隐式依赖
        "--hidden-import=pywinauto",
        "--hidden-import=pywinauto.findwindows",
        "--hidden-import=PIL",
        # 打包 configs 目录
        "--add-data", f"{project_root / 'configs'}{os.pathsep}configs",
    ]

    if args.onefile:
        cmd.append("--onefile")
    if args.no_console:
        cmd.append("--noconsole")

    print(f"[BUILD] PyInstaller 命令: {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=project_root)


def main() -> int:
    args = parse_args()
    check_platform()

    if args.clean:
        clean()

    # 默认走 Nuitka
    use_nuitka = args.nuitka or not args.pyinstaller

    if use_nuitka:
        print("[BUILD] 使用 Nuitka")
        return build_with_nuitka(args)
    else:
        print("[BUILD] 使用 PyInstaller")
        return build_with_pyinstaller(args)


if __name__ == "__main__":
    import os  # 用于 os.pathsep
    sys.exit(main())
