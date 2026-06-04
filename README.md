# OneInstall · 一键自动安装器

> **核心目标**：把 `M:\考试资源\安装\1.exe` 改成全自动安装，处理"下一步"等向导无需人工干预，全程日志可追溯。

---

## 1. 这是什么

**OneInstall** 是一款 Windows 端"傻瓜式"自动安装器，专为考场/机房场景设计：

| 场景 | 痛点 | OneInstall 解决方案 |
|------|------|---------------------|
| **exe 经常变** | 不同考试用不同软件，每次都要手动点 | 配置驱动 + GUI 自适应，无需改代码 |
| **向导流程繁琐** | 每个安装程序都有"下一步/同意/安装路径"等页面 | pywinauto 多策略匹配，全自动跳过 |
| **静默安装失败** | 很多软件不支持 `/S` 等静默参数 | 静默失败后自动降级到 GUI 模式 |
| **出问题难排查** | 不知道卡在哪一步、为什么失败 | 分级日志 + 失败自动截图 |

**核心特性**：
- ✅ **三层自适应策略**：静默参数 → 控件名匹配 → 启发式点击
- ✅ **配置驱动**：新软件加 YAML 配置即可，不用改代码
- ✅ **完整日志**：DEBUG/INFO/WARN/ERROR 分级 + 时间滚动
- ✅ **失败可溯**：失败时自动截图保存到 `screenshots/`
- ✅ **单文件 EXE**：用 Nuitka 打包成单个 .exe，丢到 M:\ 即可分发

---

## 2. 快速开始

### 2.1 直接使用（已经有编译好的 EXE）

```
1. 把你这次的安装包重命名为 1.exe
2. 放到 M:\考试资源\安装\1.exe
3. 双击 OneInstall.exe
4. 等待日志显示「安装流程结束」即可
```

### 2.2 源码运行（开发/调试用）

```bash
# Windows 环境
git clone <repo>
cd oneinstall
pip install -r requirements.txt
python main.py
```

---

## 3. 配置文件

### 3.1 默认配置 `configs/default.yaml`

`default.yaml` 是兜底配置，覆盖主流安装程序的中英文按钮名。

```yaml
# 静默安装参数，按顺序尝试，第一个成功就停
silent_args:
  - /S
  - /VERYSILENT
  - /quiet
  - /qn

# 安装程序类型自动识别（启发式）
installer_type: auto  # auto | inno_setup | nsis | msi | installshield

# GUI 模式下的按钮匹配（中英文 + 容错）
wizard_buttons:
  - names: [下一步, Next, 下一步(N)>, &Next]
    action: click
  - names: [我同意, I Agree, 接受, Accept, &Accept]
    action: click
  - names: [安装, Install, 安装(I)>, &Install]
    action: click
  - names: [完成, Finish, 完成(F)>, &Finish]
    action: install_done  # 标记为"完成"按钮

# 跳过错误继续点（对部分安装程序有效）
skip_on_error: true

# 总超时（秒）
timeout: 600
```

### 3.2 特殊软件配置

如果某个软件有特殊流程，复制 `default.yaml` 改个名就行：

```bash
cp configs/default.yaml configs/my_special_app.yaml
# 编辑 my_special_app.yaml
```

配置文件名 → 匹配规则：
- `default.yaml` — 兜底
- `*.yaml` — 当前默认按软件指纹匹配（TODO: 后续扩展）

---

## 4. 日志系统

### 4.1 日志位置

| 类型 | 路径 | 说明 |
|------|------|------|
| 详细日志 | `logs/install_YYYYMMDD.log` | DEBUG 级别，包含每一步操作 |
| 失败截图 | `screenshots/fail_*.png` | 失败时自动截图 |

**注**：打包成 EXE 后，路径会变成 `%USERPROFILE%\OneInstall\logs\`。

### 4.2 日志格式

```
2026-06-04 14:30:15 [INFO ] 检测安装包: M:\考试资源\安装\1.exe
2026-06-04 14:30:15 [INFO ] 文件大小: 12.4 MB
2026-06-04 14:30:16 [INFO ] 尝试静默安装参数: /S
2026-06-04 14:30:20 [WARN ] 静默安装失败(退出码 1620)
2026-06-04 14:30:20 [INFO ] 启动 GUI 自动化模式
2026-06-04 14:30:23 [INFO ] 等待安装窗口出现...
2026-06-04 14:30:25 [INFO ] 找到窗口: 7-Zip Setup
2026-06-04 14:30:26 [INFO ] 点击按钮: Install
2026-06-04 14:30:28 [INFO ] 点击按钮: Finish
2026-06-04 14:30:30 [INFO ] 安装完成 ✓
```

### 4.3 日志分析工具（TODO）

未来考虑加一个 `analyze_logs.py` 工具，从日志中统计安装成功率、卡点位置等。

---

## 5. 常见问题

### Q1: 某个软件死活装不上

1. 跑一次让日志和截图保留下来
2. 找到 `screenshots/fail_*.png` 看卡在哪个界面
3. 在对应 YAML 配置里加按钮名（如 `下一步` → `下一步(N)>`）
4. 重新打包

### Q2: 杀毒软件报毒

- PyInstaller/Nuitka 打包的程序偶尔被误报
- 可以加白名单，或用代码签名证书

### Q3: exe 体积太大

- 用 Nuitka 编译（默认）：~30-50MB
- 用 PyInstaller 编译（fallback）：~80-100MB

### Q4: 安装路径能改吗

默认装到 `C:\Program Files\...`。如需指定路径，在配置里加：

```yaml
install_dir: D:\Software\MyApp
```

---

## 6. 项目结构

```
oneinstall/
├── README.md                  ← 本文件
├── DEVELOPMENT.md             ← 开发文档（给开发者看）
├── CLAUDE.md                  ← 项目宪法（给 claude 看）
├── main.py                    ← 入口
├── requirements.txt
├── installer/                 ← 核心包
│   ├── core.py                ← AutoInstaller 主类
│   ├── strategies.py          ← 多策略匹配
│   ├── log.py                 ← 日志系统
│   ├── screenshot.py          ← 截图
│   └── config.py              ← 配置加载
├── configs/                   ← 配置文件
│   └── default.yaml
├── logs/                      ← 运行时日志
├── screenshots/               ← 失败截图
└── build.py                   ← 打包脚本
```

---

## 7. 路线图

- [x] v0.1: 基础静默 + GUI 自动化 + 日志
- [ ] v0.2: 按钮 OCR 兜底（PyTesseract）
- [ ] v0.3: 安装结果校验（启动一次确认能跑）
- [ ] v0.4: Web 控制面板（远程看安装进度）
- [ ] v1.0: 完全自学习（用 LLM 分析截图判断下一步）

---

## 8. 维护

- **作者**: Boss (ztllll)
- **协作**: 飞书主会话 + tmuxbot
- **仓库**: GitHub (待创建)
