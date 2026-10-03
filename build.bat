@echo off
REM 一键打包：生成图标 + PyInstaller 单文件 exe
cd /d "%~dp0"
python gen_icon.py
python -m PyInstaller --noconfirm --onefile --windowed --icon assets/icon.ico --name ScreenTranslator main.py
echo.
echo 打包完成: dist\ScreenTranslator.exe
pause
