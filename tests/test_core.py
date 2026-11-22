# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""协议与画面拼装测试（无需图形界面）。"""

import os
import sys
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from screen_broadcast import core  # noqa: E402


class ProtocolTest(unittest.TestCase):
    def test_frame_header_roundtrip(self):
        msg = core.build_frame_header(1600, 900, 12)
        data = core.parse_message(msg)
        self.assertEqual(data['kind'], 'frame')
        self.assertEqual((data['width'], data['height'], data['id']), (1600, 900, 12))

    def test_tile_roundtrip(self):
        raw = Image.new('RGB', (64, 64), (1, 2, 3)).tobytes()
        msg = core.build_tile(3, 64, 128, raw)
        data = core.parse_message(msg)
        self.assertEqual(data['kind'], 'tile')
        self.assertEqual((data['x'], data['y'], data['id']), (64, 128, 3))
        import zlib
        self.assertEqual(zlib.decompress(data['data']), raw)

    def test_frame_end(self):
        data = core.parse_message(core.build_frame_end(9))
        self.assertEqual((data['kind'], data['id']), ('end', 9))

    def test_assembler(self):
        image = Image.new('RGB', (128, 64), 'white')
        ImageDraw.Draw(image).rectangle((70, 10, 100, 40), fill=(255, 0, 0))

        asm = core.FrameAssembler()
        self.assertIsNone(asm.feed(core.build_frame_header(128, 64, 1)))
        for x, y, tile in core.iter_changed_tiles(image, None):
            asm.feed(core.build_tile(1, x, y, tile.tobytes()))
        result = asm.feed(core.build_frame_end(1))

        self.assertIsNotNone(result)
        self.assertEqual(result.size, (128, 64))
        self.assertEqual(result.getpixel((80, 20)), (255, 0, 0))

    def test_stale_tile_is_ignored(self):
        asm = core.FrameAssembler()
        asm.feed(core.build_frame_header(64, 64, 2))
        # 上一帧（id=1）的迟到瓦片必须被丢弃
        asm.feed(core.build_tile(1, 0, 0, Image.new('RGB', (64, 64), 'red').tobytes()))
        result = asm.feed(core.build_frame_end(2))
        self.assertIsNotNone(result)
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 0))


class TileDiffTest(unittest.TestCase):
    def test_only_changed_tile(self):
        before = Image.new('RGB', (128, 128), 'white')
        after = before.copy()
        ImageDraw.Draw(after).rectangle((70, 70, 80, 80), fill='black')
        tiles = core.iter_changed_tiles(after, before)
        self.assertEqual(len(tiles), 1)
        self.assertEqual((tiles[0][0], tiles[0][1]), (64, 64))

    def test_identical_frames_send_nothing(self):
        image = Image.new('RGB', (128, 128), 'white')
        self.assertEqual(core.iter_changed_tiles(image, image), [])

    def test_size_change_sends_all(self):
        small = Image.new('RGB', (64, 64), 'white')
        big = Image.new('RGB', (128, 64), 'white')
        self.assertEqual(len(core.iter_changed_tiles(big, small)), 2)


if __name__ == '__main__':
    unittest.main()
