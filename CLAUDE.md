# CLAUDE.md — OneInstall 项目宪法

> 本文件是 `oneinstall` 项目的项目宪法，进入本 cwd 时自动加载。
> 加载顺序: `~/.claude/CLAUDE.md`（全局）→ `../CLAUDE.md`（hbhy 统筹）→ **本文件** → per-cwd memory。

---

## 0. 项目定位

**OneInstall** = Windows 一键自动安装器，专为考场/机房"exe 经常变"场景设计。

| 维度 | 内容 |
|------|------|
| 目标用户 | Boss (ztllll) + 考场学生机 |
| 部署目标 | M:\考试资源\安装\1.exe |
| 技术栈 | Python 3.11+ / pywinauto / PyYAML / Pillow / logging |
| 打包工具 | Nuitka（首选）/ PyInstaller（fallback） |
| 运行平台 | Windows 10/11 |

---

## 1. 不可违反的铁律

### 1.1 文档先行（继承全局 §3 铁律）

- **改代码先改文档**，文档是单一事实源
- `README.md` = 用户面（怎么用）
- `DEVELOPMENT.md` = 开发面（怎么改）
- 本文件 = 项目宪法（铁律）
- 三者内容必须一致，漂移即 bug

### 1.2 配置驱动（核心架构原则）

- **业务逻辑和软件配置必须解耦**
- 加新软件支持 = 加 YAML 配置，不许改 Python 代码
- 例外: 新增通用能力（按钮匹配策略等）才动代码

### 1.3 三层自适应（核心算法）

```
1. 静默参数（最快，优先）
   ↓ 失败
2. 控件名匹配（pywinauto uia backend）
   ↓ 失败
3. 启发式点击（兜底 + 截图）
```

任何安装策略都必须落在这三层之一，不要发明第 4 层。

### 1.4 失败可观测

- 每一步必须打日志（DEBUG 级别）
- 任何失败必须:
  - 写 ERROR 日志
  - 自动截图保存到 `screenshots/`
  - 截图路径回写日志
- 不允许"静默失败"

### 1.5 防御性编程

- 每个阻塞操作必须有超时
- 每个 IO 必须有异常处理
- 总超时硬上限 10 分钟（可配置）

---

## 2. 关键约束

### 2.1 不变量

- 配置文件 `configs/*.yaml` 始终是 `utf-8` 编码
- 日志目录 `logs/` 在 EXE 模式下重定向到 `%USERPROFILE%\OneInstall\logs\`
- 截图目录 `screenshots/` 同上
- 默认 exe 路径: `M:\考试资源\安装\1.exe`（可命令行覆盖）

### 2.2 禁止

- ❌ 引入 pywinauto 之外的 GUI 自动化库（pyautogui / selenium 等）
- ❌ 在代码里硬编码按钮名（中英文都通过配置文件）
- ❌ 使用 emoji 日志（保持 ASCII 友好的中文）
- ❌ 用 `print` 代替 `logger`（print 不入文件）
- ❌ `git add -A`（每次必须 `git status` 核对）

### 2.3 必须

- ✅ 所有公开函数写 type hints
- ✅ 所有公开函数写 docstring（中文）
- ✅ 改一处代码必同步改对应文档
- ✅ commit 前 `git status` + `git diff --stat` 核对

---

## 3. 必跑命令

```bash
# 跑单元测试（Linux 也能跑）
pytest tests/ -v

# 打包（Windows）
python build.py --nuitka
# 或
python build.py --pyinstaller

# 直接跑（开发模式）
python main.py

# 跑指定 exe + 指定配置
python main.py --exe "D:\downloads\app.exe" --config "configs/nsis.yaml"
```

---

## 4. 当前在途任务状态

> **这里** 实时记录当前进行中的任务上下文。
> 切换会话/压缩上下文后，新会话加载本节即可接续。

### v0.1 立项中（2026-06-04 启动）

**已完成**：
- ✅ 项目脚手架（git init + .gitignore）
- ✅ README.md / DEVELOPMENT.md / CLAUDE.md

**进行中**：
- ⏳ installer/ 包核心代码

**下一步第一个动作**：
- 写 `installer/log.py`（最独立，先写）
- 再写 `installer/config.py`（依赖 yaml）
- 再写 `installer/screenshot.py`
- 再写 `installer/strategies.py`
- 最后写 `installer/core.py` + `main.py`

---

## 5. 风险与决策记录

### 决策 1: Python + pywinauto vs PowerShell + UIAutomation

- **结论**: 选 Python + pywinauto
- **理由**: exe 经常变 → 需要强 GUI 自动化能力；pywinauto 双 backend + 多维度控件匹配
- **代价**: EXE 体积 30-100MB（用 Nuitka 可压到 30-50MB）
- **决策日期**: 2026-06-04

### 决策 2: 配置驱动 vs 代码硬编码

- **结论**: 配置驱动
- **理由**: Boss 明确说"exe 经常变"，加配置比改代码快
- **形式**: YAML，每个软件一份 `configs/<name>.yaml`

### 决策 3: 打包工具

- **首选**: Nuitka（编译成原生代码，体积小）
- **fallback**: PyInstaller（生态成熟，兼容性好）
- **自动化**: `build.py` 一键切换

---

## 6. 后续扩展点（不写代码，但记下来）

- v0.2: OCR 兜底（PyTesseract）
- v0.3: 安装结果校验（启动一次确认能跑）
- v0.4: Web 控制面板（远程看安装进度）
- v1.0: LLM 自学习（用 Claude 读截图判断下一步）

---

## 7. 维护

- **维护者**: Boss (ztllll)
- **协作**: 飞书主会话 → tmuxbot → 本 cwd
- **上游宪法**: `~/.claude/CLAUDE.md` + `/data/project/CLAUDE.md`
