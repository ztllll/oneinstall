@echo off
REM OneInstall - Windows 一键打包脚本
REM 双击运行, 5 分钟出 OneInstall.exe
REM 要求: Windows 10/11 + Python 3.11+ (python.org 装的)

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   OneInstall - Windows EXE Build
echo ============================================================
echo.

REM 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装或不在 PATH
    echo.
    echo 请先装 Python 3.11+: https://www.python.org/downloads/
    echo 安装时勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [INFO] Python 版本:
python --version
echo.

REM 检查 pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip 不可用
    pause
    exit /b 1
)

echo [STEP 1/3] 装依赖...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] 依赖装失败, 检查网络
    pause
    exit /b 1
)
echo.

echo [STEP 2/3] 编译 EXE...
echo        (这步要 2-3 分钟, 请耐心等)
echo.
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name OneInstall ^
    --distpath dist ^
    --workpath build ^
    --clean ^
    --noconfirm ^
    --hidden-import=pywinauto ^
    --hidden-import=pywinauto.findwindows ^
    --hidden-import=PIL ^
    --add-data "configs;configs" ^
    main.py
if errorlevel 1 (
    echo [ERROR] 编译失败
    pause
    exit /b 1
)
echo.

echo [STEP 3/3] 验证 EXE...
if not exist dist\OneInstall.exe (
    echo [ERROR] EXE 没生成
    pause
    exit /b 1
)

for %%I in (dist\OneInstall.exe) do set SIZE=%%~zI
set /a SIZE_MB=!SIZE! / 1048576
echo [OK] OneInstall.exe 生成成功, 大小: !SIZE_MB! MB
echo.
echo ============================================================
echo   BUILD 完毕!
echo   EXE 位置: %CD%\dist\OneInstall.exe
echo ============================================================
echo.
echo 下一步:
echo   1. 把 dist\OneInstall.exe 复制到 M:\考试资源\安装\
echo   2. 改名为 1.exe 或自定义路径
echo   3. 双击即用
echo.
echo 更多信息: 看 README.md
echo.
pause
