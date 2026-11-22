#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "[1/3] 安装依赖..."
python3 -m pip install --upgrade pyinstaller pillow

echo "[2/3] 打包发送端..."
pyinstaller --noconfirm --clean --windowed \
  --name "屏幕广播发送端" --icon "assets/sender.icns" \
  --add-data "assets:assets" app_sender.py

echo "[3/3] 打包接收端..."
pyinstaller --noconfirm --clean --windowed \
  --name "屏幕广播接收端" --icon "assets/receiver.icns" \
  --add-data "assets:assets" app_receiver.py

echo
echo "完成，输出目录：dist/"
echo "  屏幕广播发送端.app / 屏幕广播接收端.app"
echo "提示：首次运行发送端时，需要在「系统设置 → 隐私与安全性 → 屏幕录制」中授权。"
