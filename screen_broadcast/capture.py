# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""屏幕采集与平台初始化。"""

import sys


def init_platform():
    """在创建任何窗口之前调用。"""
    if sys.platform == 'win32':
        _enable_windows_dpi_awareness()


def _enable_windows_dpi_awareness():
    try:
        import ctypes
    except Exception:
        return
    for call in (
        lambda: ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)),
        lambda: ctypes.windll.shcore.SetProcessDpiAwareness(2),
        lambda: ctypes.windll.user32.SetProcessDPIAware(),
    ):
        try:
            call()
            return
        except Exception:
            continue


def grab_screen():
    """抓取主屏幕，返回 RGB 模式的 PIL.Image。"""
    try:
        from PIL import ImageGrab
        return ImageGrab.grab().convert('RGB')
    except Exception as exc:
        raise RuntimeError(capture_error_message(exc))


def capture_error_message(exc):
    if sys.platform == 'darwin':
        return ('无法截取屏幕。请在「系统设置 → 隐私与安全性 → 屏幕录制」中'
                '允许本程序（或终端）访问屏幕，然后重新启动程序。\n原始错误：%s' % exc)
    return '无法截取屏幕：%s' % exc
