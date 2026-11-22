# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""配置读取与保存。

设置由发送端界面管理，自动保存为 screen_broadcast_settings.json：
- 优先保存在程序所在目录（便于随文件夹一起移植）；
- 若该目录不可写（如 macOS 的 /Applications），回退到用户配置目录；
- 兼容旧版的 屏幕广播配置.txt（只读，作为初始值）。
"""

import json
import os
import sys

JSON_NAME = 'screen_broadcast_settings.json'
LEGACY_NAME = '屏幕广播配置.txt'

DEFAULTS = {
    'multicast': True,
    'auto': True,
    'max_width': 1600,
    'interval': 0.6,
    'keyframe': 5.0,
}


def _base_dir():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        # macOS .app: 配置文件放在 .app 所在目录（如 /Applications）
        if sys.platform == 'darwin' and exe_dir.endswith(os.path.join('Contents', 'MacOS')):
            return os.path.dirname(os.path.dirname(os.path.dirname(exe_dir)))
        return exe_dir
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _user_config_dir():
    home = os.path.expanduser('~')
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA') or os.path.join(home, 'AppData', 'Roaming')
    elif sys.platform == 'darwin':
        base = os.path.join(home, 'Library', 'Application Support')
    else:
        base = os.path.join(home, '.config')
    return os.path.join(base, '屏幕广播')


def settings_paths():
    """按优先级返回设置文件的候选路径。"""
    paths = [os.path.join(_base_dir(), JSON_NAME)]
    try:
        paths.append(os.path.join(_user_config_dir(), JSON_NAME))
    except Exception:
        pass
    return paths


def sanitize(cfg):
    result = dict(DEFAULTS)
    if 'multicast' in cfg:
        result['multicast'] = bool(cfg['multicast'])
    if 'auto' in cfg:
        result['auto'] = bool(cfg['auto'])
    for key, low, high, cast in (
        ('max_width', 320, 3840, int),
        ('interval', 0.05, 5.0, float),
        ('keyframe', 1.0, 60.0, float),
    ):
        if key in cfg:
            try:
                result[key] = min(high, max(low, cast(cfg[key])))
            except Exception:
                pass
    return result


def _parse_legacy(path):
    cfg = {}
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except Exception:
        return None
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if key in ('模式', 'mode'):
            cfg['multicast'] = not ('广播' in value or value.lower() == 'broadcast')
        elif key in ('最大宽度', 'max_width'):
            cfg['max_width'] = value
        elif key in ('帧间隔', 'interval'):
            cfg['interval'] = value
        elif key in ('关键帧间隔', 'keyframe'):
            cfg['keyframe'] = value
    return cfg or None


def load_config():
    """返回 (配置字典, 来源说明)。"""
    for path in settings_paths():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return sanitize(data), path
        except Exception:
            continue

    legacy_paths = [os.path.join(_base_dir(), LEGACY_NAME)]
    try:
        legacy_paths.append(os.path.join(os.getcwd(), LEGACY_NAME))
    except Exception:
        pass
    for path in legacy_paths:
        data = _parse_legacy(path)
        if data:
            return sanitize(data), path

    return dict(DEFAULTS), None


def save_config(cfg):
    """保存设置，返回实际写入的路径；失败返回 None。"""
    data = sanitize(cfg)
    for path in settings_paths():
        try:
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return path
        except Exception:
            continue
    return None
