# OneInstall · 开发文档

> **面向开发者**：源码结构、模块接口、设计决策、扩展指南。

---

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                       main.py (入口)                         │
│   解析参数 → 加载配置 → 启动 AutoInstaller → 等待退出        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  AutoInstaller (core.py)                     │
│   编排整个安装流程:                                         │
│     1. 策略1: 静默参数安装 (strategies.silent_install)      │
│     2. 策略2: pywinauto GUI 自动化 (strategies.gui_install) │
│     3. 失败处理: 截图 + 日志                                 │
└─────────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
┌──────────────────┐          ┌────────────────────┐
│ strategies.py    │          │ config.py          │
│                  │          │                    │
│ - silent_install │          │ - load_config()    │
│ - gui_install    │          │ - merge_config()   │
│ - find_button    │          │ - validate_config()│
│ - click_button   │          │                    │
└──────────────────┘          └────────────────────┘
        │                              │
        ▼                              ▼
┌──────────────────┐          ┌────────────────────┐
│ log.py           │          │ screenshot.py      │
│                  │          │                    │
│ - setup_logging()│          │ - save_screenshot()│
│ - rotate handler │          │ - get_active_window│
└──────────────────┘          └────────────────────┘
```

### 1.1 设计原则

1. **配置驱动** — 业务逻辑和配置分离，新软件加 YAML 即可
2. **策略可替换** — `strategies.py` 里每种安装方式是独立的，可单独替换
3. **失败可观测** — 每一步都打日志，失败时自动截图
4. **防御性编程** — 显式超时、显式异常处理、显式重试

---

## 2. 模块详细

### 2.1 `installer/core.py` — AutoInstaller 主类

```python
class AutoInstaller:
    def __init__(self, exe_path: str, config: dict):
        """初始化安装器
        :param exe_path: 目标安装包绝对路径
        :param config: 已合并的 dict 配置
        """
    
    def run(self) -> bool:
        """执行完整安装流程，返回是否成功"""
        # 1. 校验文件存在
        # 2. 尝试静默安装
        # 3. 失败则降级 GUI 模式
        # 4. 返回结果
```

### 2.2 `installer/strategies.py` — 安装策略

```python
def silent_install(exe_path: str, args_list: list[str], timeout: int) -> SilentResult:
    """按顺序尝试静默参数
    :return: SilentResult(success, exit_code, last_args)
    """

def gui_install(
    exe_path: str,
    wizard_buttons: list[dict],
    timeout: int,
    screenshot_dir: str,
) -> GuiResult:
    """GUI 模式安装：启动 exe → 循环匹配并点击按钮 → 检测完成
    核心算法:
      loop {
        1. 等待任意安装窗口出现 (pywinauto 匹配)
        2. 在窗口里多策略搜索"下一步"按钮
        3. 找到则点击, 找不到则等 1s 重试
        4. 检测是否出现"完成"按钮 → 退出循环
        5. 总超时判断
      }
    """
```

#### 按钮多策略匹配优先级

```python
BUTTON_MATCH_STRATEGIES = [
    "name_exact",      # 完全匹配按钮文字
    "name_fuzzy",      # 模糊匹配（含 "&Next"、"下一步(N)>" 等）
    "control_type",    # Button 类型 + 位置启发式
    "ocr_fallback",    # 兜底：OCR 识别（v0.2 规划）
]
```

### 2.3 `installer/log.py` — 日志系统

```python
def setup_logging(
    log_dir: str | None = None,
    level: int = logging.DEBUG,
    console_level: int = logging.INFO,
) -> logging.Logger:
    """初始化日志
    - 文件: RotatingFileHandler, 5MB × 10 备份
    - 控制台: StreamHandler
    - 格式: 时间 [级别] 消息
    """
```

#### 日志级别使用规约

| 级别 | 何时用 | 示例 |
|------|-------|------|
| DEBUG | 详细的中间步骤（文件查找、按钮扫描）| `匹配按钮: '下一步' 在窗口 'Setup'` |
| INFO | 用户关心的关键节点 | `尝试静默安装`, `安装完成 ✓` |
| WARN | 非致命问题（重试一次）| `静默安装失败, 降级 GUI 模式` |
| ERROR | 影响结果的失败 | `总超时退出`, `未找到 exe 文件` |

### 2.4 `installer/screenshot.py` — 截图

```python
def save_screenshot(
    tag: str,
    save_dir: str = "screenshots",
) -> str:
    """截全屏并保存
    :param tag: 文件名标记, e.g. "timeout" / "btn_not_found"
    :return: 保存的文件绝对路径
    """
```

### 2.5 `installer/config.py` — 配置加载

```python
def load_config(name: str = "default") -> dict:
    """加载 configs/<name>.yaml
    找不到则用 default
    """

def merge_config(base: dict, override: dict) -> dict:
    """深度合并两个配置"""

def validate_config(cfg: dict) -> tuple[bool, str]:
    """校验配置合法性, 返回 (ok, error_msg)"""
```

---

## 3. 关键算法

### 3.1 自适应按钮匹配

```python
# 伪代码
def find_next_button(window) -> Control | None:
    # 优先级 1: 精确匹配按钮名
    for name in ["下一步", "Next", "下一步(N)>", "&Next", "Install", "安装"]:
        btn = window.child_window(title=name, control_type="Button")
        if btn.exists():
            return btn
    
    # 优先级 2: 模糊匹配（含 alt 快捷键前缀 &）
    all_buttons = window.descendants(control_type="Button")
    for btn in all_buttons:
        text = btn.window_text()
        if any(kw in text for kw in ["下一步", "Next", "Install"]):
            return btn
    
    # 优先级 3: CheckBox 类型（接受协议）
    for cb in window.descendants(control_type="CheckBox"):
        text = cb.window_text()
        if "同意" in text or "Agree" in text or "Accept" in text:
            cb.check()  # 自动勾选
    
    return None
```

### 3.2 安装完成精确判断

```python
def is_install_done(window) -> bool:
    # 1. 出现"完成/Finish/Close/关闭"按钮
    done_keywords = ["完成", "Finish", "Close", "关闭", "&Finish", "完成(&F)"]
    for kw in done_keywords:
        if window.child_window(title=kw, control_type="Button").exists():
            return True
    
    # 2. 进程退出 + 窗口消失（兜底）
    if not process_running(original_pid) and not window.exists():
        return True
    
    return False
```

### 3.3 失败兜底 + 截图

```python
def handle_failure(stage: str, exc: Exception):
    logger.error(f"阶段 [{stage}] 失败: {exc}")
    path = save_screenshot(stage)
    logger.error(f"截图已保存: {path}")
    # 把截图路径也写进日志末尾
```

---

## 4. 扩展指南

### 4.1 加一种新的安装程序支持

```python
# 在 installer/strategies.py 里加一个专用函数
def install_wix_bundle(exe_path, **kwargs) -> SilentResult:
    """WiX Bundle 专用静默安装"""
    # WiX: setup.exe /quiet /log install.log
    ...
```

然后在 `core.py` 里根据 `installer_type` 分发。

### 4.2 加新的按钮匹配策略

```python
# strategies.py 里加一个策略函数
def match_by_ocr(window) -> Control | None:
    """用 OCR 识别按钮位置（v0.2 规划）"""
    img = capture_window(window)
    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
    # 解析坐标后用 pyautogui 点击
    ...
```

### 4.3 加新的日志 sink

```python
# log.py 里 setup_logging 加 handler
def setup_logging(...):
    ...
    # 飞书 webhook 推送
    if config.get("feishu_webhook"):
        handler = FeishuHandler(config["feishu_webhook"])
        logger.addHandler(handler)
```

---

## 5. 测试

### 5.1 单元测试

```bash
pytest tests/ -v
```

测试覆盖：
- `config.py` — 配置加载/合并/校验
- `strategies.py` — 按钮匹配（mock 窗口）
- `log.py` — 日志输出格式
- `screenshot.py` — 截图保存（mock 屏幕）

### 5.2 集成测试（需要 Windows + 真实安装包）

```bash
# 准备一个测试用安装包 (e.g. 7-Zip installer)
python tests/integration/test_7zip.py
```

### 5.3 跨平台开发注意事项

| 操作 | Linux/macOS | Windows |
|------|-------------|---------|
| 单元测试 | ✅ 全部能跑 | ✅ |
| pywinauto | ❌ 不可用 | ✅ |
| 打包 EXE | ❌ 需 Windows | ✅（推荐）|
| 截图 | ❌ 需 Windows | ✅ |

**结论**: 日常开发在 Linux 跑单元测试，打包/集成测试在 Windows 机器做。

---

## 6. 打包

### 6.1 Nuitka 打包（推荐）

```bash
# Windows 环境
python -m pip install nuitka
python build.py --nuitka
# 产物: dist/OneInstall.exe (~30-50MB)
```

### 6.2 PyInstaller 打包（fallback）

```bash
python -m pip install pyinstaller
python build.py --pyinstaller
# 产物: dist/OneInstall.exe (~80-100MB)
```

### 6.3 体积优化

- 用 `--onefile` 打成单文件
- 加 `--windows-disable-console` 不弹黑窗
- 用 UPX 压缩（可选）

---

## 7. 调试技巧

### 7.1 看 pywinauto 能识别哪些控件

```python
from pywinauto import Application
app = Application(backend="uia").connect(title_re=".*")
dlg = app.window(title_re=".*")
dlg.print_control_identifiers()  # 打印所有控件
```

### 7.2 日志位置（EXE 运行时）

EXE 模式下日志在：
```
%USERPROFILE%\OneInstall\logs\install_YYYYMMDD.log
```

截图在：
```
%USERPROFILE%\OneInstall\screenshots\
```

---

## 8. 设计权衡

| 决策 | 备选 | 为什么选这个 |
|------|------|-------------|
| pywinauto (uia backend) | PyAutoGUI | 精度高、可识别控件名、对向导支持好 |
| YAML 配置 | JSON / INI | 支持注释、可读性最好 |
| 同步执行 | 异步 | GUI 自动化是阻塞的，异步反而复杂 |
| 单文件 EXE | 安装包 | 简单直接，方便丢到 M:\ 共享 |
| 配置驱动 | 代码硬编码 | exe 经常变，配置化是必然 |
