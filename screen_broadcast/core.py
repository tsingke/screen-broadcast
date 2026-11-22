# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""通信协议与画面分块工具。

与配套的 Windows 版 exe 协议一致，可互相通信：

    帧头:  b'F' + struct('!HHHH', width, height, frame_id, count)
    瓦片:  b'T' + struct('!HHH', frame_id, x, y) + zlib(rgb_tile_bytes)
    帧尾:  b'D' + struct('!H', frame_id)
    结束:  b'close'
"""

import struct
import zlib

from PIL import Image, ImageChops

TILE = 64
PORT = 22222
GROUP = '239.255.42.22'
BUFFER_SIZE = 49152


def build_frame_header(width, height, frame_id, count=0):
    return b'F' + struct.pack('!HHHH', width, height, frame_id & 0xFFFF, count)


def build_tile(frame_id, x, y, rgb_bytes):
    return b'T' + struct.pack('!HHH', frame_id & 0xFFFF, x, y) + zlib.compress(rgb_bytes)


def build_frame_end(frame_id):
    return b'D' + struct.pack('!H', frame_id & 0xFFFF)


def parse_message(message):
    """解析一条 UDP 消息，返回字典或 None。"""
    if not message:
        return None
    if message == b'close':
        return {'kind': 'close'}
    tag = message[:1]
    if tag == b'F' and len(message) >= 9:
        w, h, fid, count = struct.unpack('!HHHH', message[1:9])
        return {'kind': 'frame', 'width': w, 'height': h, 'id': fid, 'count': count}
    if tag == b'T' and len(message) >= 7:
        fid, x, y = struct.unpack('!HHH', message[1:7])
        return {'kind': 'tile', 'id': fid, 'x': x, 'y': y, 'data': message[7:]}
    if tag == b'D' and len(message) >= 3:
        return {'kind': 'end', 'id': struct.unpack('!H', message[1:3])[0]}
    return None


class FrameAssembler:
    """接收端画面拼装器：把瓦片消息拼成完整画面。"""

    def __init__(self, tile=TILE):
        self.tile = tile
        self.image = None
        self.size = (0, 0)
        self.frame_id = -1
        self.dirty = False

    def feed(self, message):
        """输入一条 UDP 消息；一帧结束时返回当前画面（副本），否则返回 None。"""
        msg = parse_message(message)
        if msg is None:
            return None
        kind = msg['kind']
        if kind == 'frame':
            w, h = msg['width'], msg['height']
            if w <= 0 or h <= 0:
                return None
            self.frame_id = msg['id']
            if self.image is None or (w, h) != self.size:
                self.image = Image.new('RGB', (w, h))
                self.size = (w, h)
                self.dirty = True
            return None
        if kind == 'tile':
            if self.image is None or msg['id'] != self.frame_id:
                return None
            x, y = msg['x'], msg['y']
            tw = min(self.tile, self.size[0] - x)
            th = min(self.tile, self.size[1] - y)
            if tw <= 0 or th <= 0:
                return None
            try:
                tile = Image.frombytes('RGB', (tw, th), zlib.decompress(msg['data']))
            except Exception:
                return None
            self.image.paste(tile, (x, y))
            self.dirty = True
            return None
        if kind == 'end':
            if msg['id'] == self.frame_id and self.dirty and self.image is not None:
                self.dirty = False
                return self.image.copy()
            return None
        return None


def iter_changed_tiles(image, previous, tile=TILE):
    """返回需要发送的瓦片列表 [(x, y, tile_image), ...]。

    previous 为 None 或尺寸不同时返回全部瓦片（关键帧）。
    """
    width, height = image.size
    diff = None
    if previous is not None and previous.size == image.size:
        diff = ImageChops.difference(image, previous)
    tiles = []
    for y in range(0, height, tile):
        for x in range(0, width, tile):
            box = (x, y, min(x + tile, width), min(y + tile, height))
            if diff is not None:
                if diff.crop(box).getbbox() is None:
                    continue
            tiles.append((x, y, image.crop(box)))
    return tiles
