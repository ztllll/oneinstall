# Changelog · OneInstall

> 按 [Keep a Changelog](https://keepachangelog.com/) 规范. 版本号遵循 [SemVer](https://semver.org/).

---

## [Unreleased]

### 计划中
- v0.2: OCR 兜底（PyTesseract）
- v0.3: 安装结果校验
- v0.4: Web 控制面板

---

## [0.1.0] - 2026-06-04

### ✨ 新增 (Added)
- 项目脚手架（git + .gitignore + 目录结构）
- `installer/core.py` — AutoInstaller 主类
- `installer/strategies.py` — 静默安装 + GUI 自动化策略
- `installer/log.py` — 分级日志 + 时间滚动
- `installer/screenshot.py` — 失败自动截图
- `installer/config.py` — YAML 配置驱动
- `main.py` — 命令行入口（argparse）
- `build.py` — Nuitka/PyInstaller 打包脚本
- `build.bat` — Windows 一键打包脚本
- `appveyor.yml` — AppVeyor CI 配置（备选）
- `.github/workflows/build.yml` — GitHub Actions 配置
- 4 份配置: `default.yaml` / `inno_setup.yaml` / `nsis.yaml` / `quiet_mode.yaml`
- 完整文档: README / DEVELOPMENT / CLAUDE.md

### 🎯 核心特性
- **三层自适应**: 静默参数 → 控件名匹配 → 启发式点击
- **配置驱动**: 加新软件 = 加 YAML，零代码改动
- **失败可观测**: 分级日志 + 失败截图回写
- **跨平台开发**: Linux 跑单元测试，Windows 跑 GUI 集成
- **跨平台编译**: Linux + Wine 出 Windows EXE（实测成功）

### 🐛 修复 (Fixed)
- EXE 模式强制 UTF-8 stdout/stderr（解决 Windows cp1252 编码报错）
- EXE 模式 configs 目录改用 _MEIPASS（PyInstaller 临时目录）

### 📦 EXE 产物
- **v0.1.0**: https://github.com/ztllll/oneinstall/releases/download/v0.1.0/OneInstall-v0.1.0.exe
- 编译环境: pyadmin (Ubuntu 22.04) + Wine 6.0.3 + Python 3.11.9 + PyInstaller 6.20.0
- 编译时间: < 3 分钟

### 🧪 测试
- 单元 smoke test 全部通过（包导入/配置加载/日志输出/截图/策略降级）
- EXE 验证: --list-configs / --help 全部正常

### 📝 文档
- README.md — 用户面（怎么用）
- DEVELOPMENT.md — 开发面（怎么改）
- CLAUDE.md — 项目宪法（铁律）
- CHANGELOG.md — 版本台账（本文件）

---

## 版本台账

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-06-13 | 0.1.0 | 出首个 EXE 产物，跨平台编译跑通 |
| 2026-06-04 | 0.1.0-dev | 立项，基础功能可用 |
