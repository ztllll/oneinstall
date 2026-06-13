"""installer.config - 配置加载/合并/校验

按 CLAUDE.md §1.2 铁律: 配置驱动, 加新软件 = 加 YAML, 不改代码.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

# 配置 schema 校验 - 用最朴素的字典键检查, 不引入 pydantic 等重依赖
DEFAULT_CONFIG: dict[str, Any] = {
    # 静默参数按顺序尝试
    "silent_args": [
        "/S",
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/silent",
        "/quiet",
        "/qn",
        "/passive",
    ],
    # 安装程序类型: auto | inno_setup | nsis | msi | installshield | wix
    "installer_type": "auto",
    # GUI 模式按钮匹配规则
    "wizard_buttons": [
        # 协议勾选 - 放在最前面, 因为有些向导会先弹协议
        {"names": ["我接受", "I accept", "我同意", "I Agree", "接受", "Accept", "&Accept"],
         "action": "check", "control_type": "CheckBox"},
        # 下一步/安装
        {"names": ["下一步", "Next", "下一步(N)>", "&Next", "下一步(&N)>"],
         "action": "click", "control_type": "Button"},
        {"names": ["安装", "Install", "安装(I)>", "&Install", "安装(&I)>"],
         "action": "click", "control_type": "Button"},
        # 完成
        {"names": ["完成", "Finish", "完成(F)>", "&Finish", "完成(&F)>", "Close", "关闭"],
         "action": "click", "control_type": "Button", "is_done": True},
    ],
    # 跳过单个按钮点击错误继续
    "skip_on_error": True,
    # 总超时(秒)
    "timeout": 600,
    # 单步超时(秒)
    "step_timeout": 30,
    # 失败截图目录
    "screenshot_dir": "screenshots",
    # 调试模式: 开启后每步截图
    "debug_screenshot": False,
}


def _config_dir() -> Path:
    """配置文件目录.

    - EXE 模式: PyInstaller 把 configs 嵌到 _MEIPASS/configs/
    - 开发模式: 项目根目录的 configs/
    - EXE 同目录 (fallback): 让用户可以覆盖配置
    """
    if getattr(__import__("sys"), "frozen", False):
        # 打包后: 优先 _MEIPASS (PyInstaller 临时目录), fallback 到 EXE 同目录
        meipass = getattr(__import__("sys"), "_MEIPASS", None)
        if meipass:
            return Path(meipass) / "configs"
        return Path(__import__("sys").executable).parent / "configs"
    # 开发模式: 项目根目录的 configs/
    return Path(__file__).resolve().parent.parent / "configs"


def load_config(name: str = "default") -> dict[str, Any]:
    """加载指定名称的配置, 找不到则返回默认配置.

    Args:
        name: 配置文件名(不含 .yaml), 如 "default" / "nsis"

    Returns:
        合并了默认值的配置 dict
    """
    base = copy.deepcopy(DEFAULT_CONFIG)
    cfg_path = _config_dir() / f"{name}.yaml"

    if not cfg_path.exists():
        # 找不到就用默认, 警告即可
        # 延迟到 logger 初始化后再打 warn, 这里先返回 base
        return base

    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        # 配置错误不应该让程序挂, 用默认 + 警告
        print(f"[WARN ] 配置文件 {cfg_path} 解析失败: {exc}, 用默认配置", flush=True)
        return base

    return merge_config(base, user_cfg)


def merge_config(base: dict, override: dict) -> dict:
    """深度合并两个 dict, override 覆盖 base.

    list 整体替换(不递归合并), 因为按钮列表是配置驱动的核心数据.
    """
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = merge_config(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


def validate_config(cfg: dict) -> tuple[bool, str]:
    """校验配置合法性.

    Returns:
        (ok, error_msg) - ok=True 时 error_msg 为空
    """
    if not isinstance(cfg, dict):
        return False, "配置根必须是 dict"

    # timeout 必须正整数
    timeout = cfg.get("timeout", 0)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        return False, f"timeout 必须正数, 当前: {timeout}"

    # wizard_buttons 必须是 list
    buttons = cfg.get("wizard_buttons", [])
    if not isinstance(buttons, list):
        return False, "wizard_buttons 必须是 list"

    for i, btn in enumerate(buttons):
        if not isinstance(btn, dict):
            return False, f"wizard_buttons[{i}] 必须是 dict"
        if "names" not in btn or not isinstance(btn["names"], list):
            return False, f"wizard_buttons[{i}].names 必须是 list"
        if "action" not in btn:
            return False, f"wizard_buttons[{i}].action 必填"
        if btn["action"] not in ("click", "check"):
            return False, f"wizard_buttons[{i}].action 必须是 click 或 check"

    return True, ""


def list_configs() -> list[str]:
    """列出 configs/ 下所有 yaml 配置名(不含扩展名)."""
    cfg_dir = _config_dir()
    if not cfg_dir.exists():
        return []
    return sorted(p.stem for p in cfg_dir.glob("*.yaml"))
