# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""发送端窗口与广播线程。"""

import socket
import threading
import time
import tkinter as tk
from tkinter import messagebox

from PIL import Image

from . import capture, config, core, ui


class ReceiverCounter:
    """监听接收端心跳（UDP 22223），统计最近 window 秒内的在线台数。"""

    def __init__(self, port=22223):
        self.port = port
        self._seen = {}
        self._lock = threading.Lock()
        self._sock = None
        self._start()

    def _start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass
        try:
            sock.bind(('', self.port))
        except OSError:
            sock.close()
            return
        sock.settimeout(0.5)
        self._sock = sock
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while True:
            try:
                data, addr = self._sock.recvfrom(64)
            except socket.timeout:
                continue
            except OSError:
                return
            if data.startswith(b'H'):
                with self._lock:
                    self._seen[addr[0]] = time.monotonic()

    def count(self, window=12.0):
        now = time.monotonic()
        with self._lock:
            for ip, ts in list(self._seen.items()):
                if now - ts > window:
                    del self._seen[ip]
            return len(self._seen)


def choose_preset(count, cfg):
    """根据在线接收端数量返回 (采集宽度, 帧间隔)。"""
    if not cfg.get('auto') or count <= 0:
        return cfg['max_width'], cfg['interval']
    if count <= 40:
        return 1920, 0.5
    if count <= 80:
        return 1600, 0.6
    return 1280, 0.8


def open_settings(root, cfg, font, scale, on_saved):
    """广播设置对话框。"""
    def u(value):
        return int(round(value * scale))

    win = tk.Toplevel(root)
    win.title('广播设置')
    win.configure(bg='white')
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()
    win.geometry('%dx%d+%d+%d' % (
        u(380), u(340),
        root.winfo_rootx() + u(30), root.winfo_rooty() + u(30)))

    mode = tk.StringVar(value='组播' if cfg['multicast'] else '广播')
    width = tk.StringVar(value=str(cfg['max_width']))
    interval = tk.StringVar(value=str(cfg['interval']))
    keyframe = tk.StringVar(value=str(cfg['keyframe']))
    auto = tk.BooleanVar(value=bool(cfg.get('auto', True)))

    tk.Label(win, text='广播设置', bg='white', fg=ui.FG,
             font=(font, 13, 'bold')).place(x=u(24), y=u(18))
    tk.Label(win, text='设置会自动保存，下次启动继续生效', bg='white', fg=ui.SUB,
             font=(font, 8)).place(x=u(25), y=u(48))

    tk.Label(win, text='传输模式', bg='white', fg=ui.FG,
             font=(font, 10)).place(x=u(24), y=u(84))
    tk.Radiobutton(win, text='组播（推荐）', variable=mode, value='组播',
                   bg='white', fg=ui.FG, activebackground='white',
                   font=(font, 9)).place(x=u(120), y=u(80))
    tk.Radiobutton(win, text='广播', variable=mode, value='广播',
                   bg='white', fg=ui.FG, activebackground='white',
                   font=(font, 9)).place(x=u(240), y=u(80))

    tk.Label(win, text='采集宽度', bg='white', fg=ui.FG,
             font=(font, 10)).place(x=u(24), y=u(124))
    tk.Entry(win, textvariable=width, width=8, font=(font, 10)).place(x=u(120), y=u(121))
    tk.Label(win, text='像素（1600 推荐）', bg='white', fg=ui.SUB,
             font=(font, 8)).place(x=u(205), y=u(125))

    tk.Label(win, text='帧间隔', bg='white', fg=ui.FG,
             font=(font, 10)).place(x=u(24), y=u(164))
    tk.Entry(win, textvariable=interval, width=8, font=(font, 10)).place(x=u(120), y=u(161))
    tk.Label(win, text='秒（0.6 约 1.5 帧/秒）', bg='white', fg=ui.SUB,
             font=(font, 8)).place(x=u(205), y=u(165))

    tk.Label(win, text='关键帧间隔', bg='white', fg=ui.FG,
             font=(font, 10)).place(x=u(24), y=u(204))
    tk.Entry(win, textvariable=keyframe, width=8, font=(font, 10)).place(x=u(120), y=u(201))
    tk.Label(win, text='秒（用于丢包自愈）', bg='white', fg=ui.SUB,
             font=(font, 8)).place(x=u(205), y=u(205))

    tk.Checkbutton(win, text='按在线接收端数量自动调节分辨率与帧率（推荐）', variable=auto,
                   bg='white', fg=ui.FG, activebackground='white',
                   font=(font, 9)).place(x=u(22), y=u(238))

    tk.Label(win, text='传输模式修改后，需停止并重新开始广播才会生效', bg='white',
             fg='#A7B0C0', font=(font, 8)).place(x=u(24), y=u(268))

    def restore_defaults():
        mode.set('组播' if config.DEFAULTS['multicast'] else '广播')
        width.set(str(config.DEFAULTS['max_width']))
        interval.set(str(config.DEFAULTS['interval']))
        keyframe.set(str(config.DEFAULTS['keyframe']))

    def save():
        try:
            values = {
                'multicast': mode.get() == '组播',
                'max_width': int(float(width.get())),
                'interval': float(interval.get()),
                'keyframe': float(keyframe.get()),
                'auto': bool(auto.get()),
            }
        except ValueError:
            messagebox.showerror('广播设置', '请输入有效的数字。', parent=win)
            return
        cfg.update(config.sanitize(values))
        path = config.save_config(cfg)
        on_saved(path)
        win.destroy()

    tk.Button(win, text='恢复默认', command=restore_defaults, bg='white', fg=ui.SUB,
              relief='flat', bd=0, highlightthickness=0, font=(font, 9),
              cursor='hand2').place(x=u(24), y=u(300), width=u(90), height=u(30))
    tk.Button(win, text='取消', command=win.destroy, bg=ui.GREY, fg=ui.GREY_FG,
              relief='flat', bd=0, highlightthickness=0, font=(font, 9),
              cursor='hand2').place(x=u(190), y=u(300), width=u(70), height=u(30))
    tk.Button(win, text='保存', command=save, bg=ui.BLUE, fg='white',
              activebackground=ui.BLUE_D, activeforeground='white', relief='flat',
              bd=0, highlightthickness=0, font=(font, 9, 'bold'),
              cursor='hand2').place(x=u(270), y=u(300), width=u(86), height=u(30))


def main():
    capture.init_platform()
    cfg, _source = config.load_config()

    root = tk.Tk()
    root.title('屏幕广播发送端')
    scale = ui.init_ui_scale(root)

    def u(value):
        return int(round(value * scale))

    root.geometry('%dx%d+%d+%d' % (u(440), u(230), u(520), u(240)))
    root.resizable(False, False)
    root.configure(bg=ui.BG)

    font = ui.font_family()
    icon64 = ui.load_photo(root, 'sender_64.png')
    icon32 = ui.load_photo(root, 'sender_32.png')
    if icon64 is not None:
        try:
            root.iconphoto(True, icon64, icon32 if icon32 is not None else icon64)
        except Exception:
            pass

    sending = threading.Event()
    counter = ReceiverCounter()
    state = {'count': 0}

    def set_status(text, color):
        def apply():
            lb_status.config(text=text, fg=color)
        try:
            root.after(0, apply)
        except Exception:
            pass

    def footer_text():
        mode = '组播' if cfg['multicast'] else '广播'
        address = core.GROUP if cfg['multicast'] else '255.255.255.255'
        width, interval = choose_preset(state['count'], cfg)
        return '在线接收端 %d 台 · %s %s:%d · %d 宽 · %.2f 秒/帧' % (
            state['count'], mode, address, core.PORT, width, interval)

    def refresh_footer():
        try:
            lb_footer.config(text=footer_text())
        except Exception:
            pass

    def tick():
        state['count'] = counter.count()
        refresh_footer()
        root.after(2000, tick)

    def stop_with_error(message):
        sending.clear()
        btn_start['state'] = 'normal'
        btn_stop['state'] = 'disabled'
        set_status('● 无法采集屏幕', ui.RED)
        messagebox.showerror('屏幕广播发送端', message)

    def broadcast():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
        except OSError:
            pass
        if cfg['multicast']:
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            except OSError:
                pass
            target = core.GROUP
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
            target = '255.255.255.255'

        frame_id = 0
        previous = None
        last_key = 0.0
        while sending.is_set():
            try:
                image = capture.grab_screen()
            except Exception as exc:
                root.after(0, lambda e=exc: stop_with_error(str(e)))
                break
            eff_width, eff_interval = choose_preset(counter.count(), cfg)
            if image.width > eff_width:
                new_h = max(1, int(image.height * eff_width / float(image.width)))
                image = image.resize((eff_width, new_h), Image.LANCZOS)
            width, height = image.size
            now = time.monotonic()
            keyframe = (previous is None or previous.size != (width, height) or
                        (now - last_key) >= cfg['keyframe'])
            if keyframe:
                last_key = now
            frame_id = (frame_id + 1) & 0xFFFF
            try:
                sock.sendto(core.build_frame_header(width, height, frame_id), (target, core.PORT))
                for x, y, tile in core.iter_changed_tiles(image, None if keyframe else previous):
                    sock.sendto(core.build_tile(frame_id, x, y, tile.tobytes()),
                                (target, core.PORT))
                sock.sendto(core.build_frame_end(frame_id), (target, core.PORT))
            except OSError:
                pass
            previous = image
            time.sleep(eff_interval)
        try:
            sock.sendto(b'close', (target, core.PORT))
        except OSError:
            pass
        sock.close()

    def on_settings_saved(path):
        lb_footer.config(text=footer_text())
        if path is None:
            messagebox.showwarning('广播设置', '设置已在本次运行中生效，但保存失败（目录不可写）。')
        else:
            set_status('● 设置已保存', '#2F9E6E')

    def start_broadcast():
        if sending.is_set():
            return
        sending.set()
        threading.Thread(target=broadcast, daemon=True).start()
        btn_start['state'] = 'disabled'
        btn_stop['state'] = 'normal'
        lb_status.config(text='● 正在广播…', fg=ui.RED)

    def stop_broadcast():
        sending.clear()
        btn_start['state'] = 'normal'
        btn_stop['state'] = 'disabled'
        lb_status.config(text='● 已停止', fg='#98A2B3')

    if icon64 is not None:
        tk.Label(root, image=icon64, bg=ui.BG, bd=0).place(
            x=u(22), y=u(20), width=u(64), height=u(64))
    tk.Label(root, text='屏幕广播发送端', bg=ui.BG, fg=ui.FG,
             font=(font, 15, 'bold')).place(x=u(104), y=u(24))
    tk.Label(root, text='将本机屏幕实时广播到学生端', bg=ui.BG, fg=ui.SUB,
             font=(font, 9)).place(x=u(105), y=u(58))

    tk.Button(root, text='设置', command=lambda: open_settings(
        root, cfg, font, scale, on_settings_saved), bg=ui.GREY, fg=ui.GREY_FG,
        activebackground='#DDE3EF', activeforeground=ui.GREY_FG, relief='flat',
        bd=0, highlightthickness=0, font=(font, 9), cursor='hand2').place(
        x=u(358), y=u(22), width=u(60), height=u(28))

    lb_status = tk.Label(root, text='● 未开始广播', bg=ui.BG, fg='#98A2B3',
                         font=(font, 10))
    lb_status.place(x=u(26), y=u(108))

    btn_start = tk.Button(root, text='开始广播', command=start_broadcast,
                          bg=ui.BLUE, fg='white', activebackground=ui.BLUE_D,
                          activeforeground='white', relief='flat', bd=0,
                          highlightthickness=0, cursor='hand2',
                          disabledforeground='#B9C7E8', font=(font, 10, 'bold'))
    btn_start.place(x=u(24), y=u(146), width=u(186), height=u(42))

    btn_stop = tk.Button(root, text='停止广播', command=stop_broadcast,
                         bg=ui.GREY, fg=ui.GREY_FG, activebackground='#DDE3EF',
                         activeforeground=ui.GREY_FG, relief='flat', bd=0,
                         highlightthickness=0, cursor='hand2',
                         disabledforeground='#AEB6C6', font=(font, 10))
    btn_stop['state'] = 'disabled'
    btn_stop.place(x=u(230), y=u(146), width=u(186), height=u(42))

    lb_footer = tk.Label(root, text=footer_text(), bg=ui.BG, fg='#A7B0C0',
                         font=(font, 8))
    lb_footer.place(x=u(26), y=u(200))

    root.after(500, tick)
    root.mainloop()
