# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""界面公共资源：配色、字体、图标。"""

import os
import sys
import tkinter as tk

BG = '#F5F7FB'
FG = '#1B2437'
SUB = '#8A93A6'
BLUE = '#2F6BFF'
BLUE_D = '#1F55E0'
GREY = '#E9EDF6'
GREY_FG = '#455066'
RED = '#E5484D'
DARK_BG = '#0B0E14'


def font_family():
    if sys.platform == 'win32':
        return 'Microsoft YaHei UI'
    if sys.platform == 'darwin':
        return 'PingFang SC'
    return 'Noto Sans CJK SC'


def asset_path(name):
    if getattr(sys, '_MEIPASS', None):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'assets', name)


def load_photo(root, name):
    """加载 assets 下的 PNG 为 Tk 图片，失败返回 None。"""
    try:
        return tk.PhotoImage(master=root, file=asset_path(name))
    except Exception:
        return None


def init_ui_scale(root):
    """Windows 高 DPI 下按比例缩放像素布局；其他平台返回 1.0。"""
    if sys.platform == 'win32':
        try:
            dpi = root.winfo_fpixels('1i')
            root.tk.call('tk', 'scaling', dpi / 72.0)
            return max(1.0, dpi / 96.0)
        except Exception:
            return 1.0
    return 1.0
