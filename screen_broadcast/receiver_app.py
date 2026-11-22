# Copyright (c) 2026 tsingke <tsingke@hotmail.com>
# SPDX-License-Identifier: MIT

"""接收端窗口与接收线程。"""

import socket
import threading
import time
import tkinter as tk

from PIL import Image, ImageTk

from . import capture, core, ui


def main():
    capture.init_platform()

    root = tk.Tk()
    root.title('屏幕广播接收端')
    root.configure(bg=ui.DARK_BG)
    root.attributes('-topmost', True)
    root.attributes('-fullscreen', True)

    font = ui.font_family()
    icon64 = ui.load_photo(root, 'receiver_64.png')
    icon32 = ui.load_photo(root, 'receiver_32.png')
    if icon64 is not None:
        try:
            root.iconphoto(True, icon64, icon32 if icon32 is not None else icon64)
        except Exception:
            pass

    display = tk.Label(root, bg=ui.DARK_BG, bd=0)
    display.pack(fill=tk.BOTH, expand=tk.YES)

    hint = tk.Label(root, text='等待教师端屏幕广播…', bg=ui.DARK_BG, fg='#5E6A7D',
                    font=(font, 12))
    hint.place(relx=0.5, rely=0.5, anchor='center')

    receiving = threading.Event()
    receiving.set()
    assembler = core.FrameAssembler()

    def show_image(image):
        try:
            width = root.winfo_width()
            height = root.winfo_height()
            w, h = image.size
            if w > 0 and h > 0:
                scale = min(width / float(w), height / float(h))
                size = (max(1, int(w * scale)), max(1, int(h * scale)))
                if size != (w, h):
                    image = image.resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(image, master=root)
            display.configure(image=photo)
            display.image = photo
            hint.place_forget()
        except Exception:
            pass

    def recv_image():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
        except OSError:
            pass
        try:
            sock.bind(('', core.PORT))
        except OSError:
            return
        try:
            mreq = socket.inet_aton(core.GROUP) + socket.inet_aton('0.0.0.0')
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except OSError:
            pass
        sock.settimeout(0.5)
        heartbeat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        last_beat = 0.0
        sender_ip = None
        while receiving.is_set():
            try:
                message, addr = sock.recvfrom(core.BUFFER_SIZE)
            except socket.timeout:
                continue
            except OSError:
                break
            sender_ip = addr[0]
            now = time.monotonic()
            if sender_ip and now - last_beat >= 3.0:
                last_beat = now
                try:
                    heartbeat.sendto(b'H', (sender_ip, 22223))
                except OSError:
                    pass
            if message == b'close':
                continue
            image = assembler.feed(message)
            if image is not None:
                threading.Thread(target=show_image, args=(image,), daemon=True).start()
        sock.close()
        heartbeat.close()

    def close_window():
        receiving.clear()
        try:
            root.destroy()
        except Exception:
            pass

    root.protocol('WM_DELETE_WINDOW', close_window)
    root.bind('<Escape>', lambda event: close_window())

    threading.Thread(target=recv_image, daemon=True).start()
    root.mainloop()
