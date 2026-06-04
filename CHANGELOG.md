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
- 4 份配置: `default.yaml` / `inno_setup.yaml` / `nsis.yaml` / `quiet_mode.yaml`
- 完整文档: README / DEVELOPMENT / CLAUDE.md

### 🎯 核心特性
- **三层自适应**: 静默参数 → 控件名匹配 → 启发式点击
- **配置驱动**: 加新软件 = 加 YAML，零代码改动
- **失败可观测**: 分级日志 + 失败截图回写
- **跨平台开发**: Linux 跑单元测试，Windows 跑 GUI 集成

### 🧪 测试
- 单元 smoke test 全部通过（包导入/配置加载/日志输出/截图/策略降级）

### 📝 文档
- README.md — 用户面（怎么用）
- DEVELOPMENT.md — 开发面（怎么改）
- CLAUDE.md — 项目宪法（铁律）
- CHANGELOG.md — 版本台账（本文件）

---

## 版本台账

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-06-04 | 0.1.0 | 立项，基础功能可用 |
