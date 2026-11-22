@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0.."

echo [1/3] 安装依赖...
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller pillow || goto :error

echo [2/3] 打包发送端...
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name "屏幕广播发送端" --icon "assets\sender.ico" ^
  --add-data "assets;assets" app_sender.py || goto :error

echo [3/3] 打包接收端...
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name "屏幕广播接收端" --icon "assets\receiver.ico" ^
  --add-data "assets;assets" app_receiver.py || goto :error

echo.
echo 完成，输出目录：dist\
echo   屏幕广播发送端.exe / 屏幕广播接收端.exe
echo 提示：请把「屏幕广播配置.txt」与发送端 exe 放在同一目录。
pause
exit /b 0

:error
echo.
echo 打包失败，请检查 Python / PyInstaller 是否安装正确。
pause
exit /b 1
