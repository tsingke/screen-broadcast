# 屏幕广播（跨平台源码版）

基于 Python + Tkinter + Pillow 的局域网屏幕广播工具，教师端广播本机屏幕，学生端实时全屏接收。
**Windows 与 macOS 均同时支持发送端和接收端**，两端可以混用。

采用 UDP **组播 + 64×64 瓦片增量传输**，适合百兆网络、100 台以上的机房环境。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-2F6BFF)
![Python](https://img.shields.io/badge/python-3.8%2B-3776AB)
![Protocol](https://img.shields.io/badge/UDP-multicast%20%2B%20tile%20delta-12B886)

<p align="center">
  <img src="assets/sender_256.png" width="88" alt="发送端">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/receiver_256.png" width="88" alt="接收端">
</p>

## 下载

从 [Releases](https://github.com/tsingke/screen-broadcast/releases) 获取安装包，无需安装 Python：

| 平台 | 文件 |
|---|---|
| Windows | `ScreenBroadcast-Windows-Sender.exe` / `ScreenBroadcast-Windows-Receiver.exe` |
| macOS（Apple Silicon） | `ScreenBroadcast-macOS-arm64.dmg` |

也可以直接运行源码（见下方「快速开始」）。

## 功能特点

- 屏幕实时广播，默认组播（可切换为广播），避免交换机广播风暴抑制
- 瓦片增量：只发送画面中变化的 64×64 区域，静态 PPT/文档时每台带宽 **< 1 Mbps**
- 每 5 秒自动关键帧：丢包自愈、中途开机的学生端自动补齐画面
- **设置内置在发送端界面**，点击「设置」即可修改，自动保存，无需手工编辑配置文件
- **智能模式**：接收端定期上报心跳，发送端按在线台数自动调节分辨率与帧率
- 接收端全屏显示，等比缩放；分辨率一致时逐像素 1:1；按 Esc 退出
- Windows 高 DPI 适配（Per-Monitor V2）
- 协议与已打包的 Windows exe 完全一致，可互相通信

## 目录结构

```
屏幕广播项目/
├── app_sender.py            # 发送端入口
├── app_receiver.py          # 接收端入口
├── screen_broadcast/
│   ├── core.py              # 协议、瓦片差分、画面拼装
│   ├── config.py            # 设置读取/保存（JSON）
│   ├── capture.py           # 屏幕采集、DPI 初始化
│   ├── ui.py                # 配色、字体、图标
│   ├── sender_app.py        # 发送端界面、设置对话框、广播线程
│   └── receiver_app.py      # 接收端界面、接收线程、心跳
├── assets/                  # 图标（PNG / ICO / ICNS）
├── tests/test_core.py       # 协议与差分单元测试
├── build/
│   ├── build_windows.bat
│   └── build_macos.sh
├── requirements.txt
└── README.md
```

## 快速开始（源码运行）

需要 Python 3.8 及以上版本。

```bash
python3 -m pip install -r requirements.txt

python3 app_sender.py      # 教师机
python3 app_receiver.py    # 学生机
```

- **Windows**：首次运行接收端时，防火墙会询问是否允许网络访问，请选择“允许”。
- **macOS**：首次运行发送端需在「系统设置 → 隐私与安全性 → 屏幕录制」中授权。
- 接收端全屏显示，按 **Esc** 退出。

## 设置（在界面中完成）

教师端点击窗口右上角 **「设置」**：

| 项目 | 说明 |
|---|---|
| 传输模式 | 组播（推荐）/ 广播 |
| 采集宽度 | 1280–3840 像素，默认 1600 |
| 帧间隔 | 秒，默认 0.6（约 1.5 帧/秒） |
| 关键帧间隔 | 秒，默认 5 |
| 按在线接收端数量自动调节 | 默认开启（见下） |

设置会自动保存为 `screen_broadcast_settings.json`（程序目录，不可写时保存到用户配置目录），
下次启动继续生效；**不需要手工编辑任何配置文件**。

### 智能调节规则

接收端每 3 秒向发送端上报一次心跳（UDP 22223），发送端据此统计在线台数，并自动选择：

| 在线接收端 | 采集宽度 | 帧间隔 |
|---|---|---|
| ≤ 40 台 | 1920 | 0.5 s |
| 41–80 台 | 1600 | 0.6 s |
| > 80 台 | 1280 | 0.8 s |
| 0 台（尚无学生上线） | 使用手动设置 | 使用手动设置 |

发送端窗口底部会显示「在线接收端 N 台」与当前实际参数。
若不希望自动调节，可在设置中取消勾选。

> 兼容旧版：若程序目录存在旧的 `屏幕广播配置.txt`，会作为初始值读取；
> 在界面保存一次后即改用 JSON，之后不再依赖该 txt。

## 打包发布

打包必须在目标系统上进行。

### Windows

双击 `build\build_windows.bat`，输出 `dist\屏幕广播发送端.exe`、`dist\屏幕广播接收端.exe`。

### macOS

```bash
bash build/build_macos.sh
```

输出 `dist/屏幕广播发送端.app`、`dist/屏幕广播接收端.app`。
对外分发建议签名/公证，否则 Gatekeeper 会提示“无法验证开发者”。

## 协议

```
帧头:  b'F' + struct('!HHHH', width, height, frame_id, count)
瓦片:  b'T' + struct('!HHH', frame_id, x, y) + zlib(tile_rgb_bytes)
帧尾:  b'D' + struct('!H', frame_id)
结束:  b'close'

数据: UDP 22222（组播 239.255.42.22 或广播 255.255.255.255）
心跳: 接收端 -> 发送端 UDP 22223，内容 b'H'（每 3 秒）
瓦片: 64×64，RGB 原始像素（无损）
```

## 部署建议（100 台以上 / 百兆）

1. 所有机器处于**同一 VLAN/子网**；组播不跨网段。
2. 交换机开启 **IGMP Snooping**，组播只转发给加入的端口。
3. 学生机放行入站 **UDP 22222**：
   ```
   netsh advfirewall firewall add rule name="UDP屏幕广播" dir=in action=allow protocol=UDP localport=22222
   ```
4. 教师机放行入站 **UDP 22223**（仅用于“在线台数统计/自动调节”，不放行也不影响广播，
   只是在线台数显示为 0、自动调节不生效）：
   ```
   netsh advfirewall firewall add rule name="UDP屏幕广播心跳" dir=in action=allow protocol=UDP localport=22223
   ```
5. 同一网段只运行一个发送端。
6. 建议先小范围（10–20 台）验证，再全量部署。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

## 常见问题

**收不到画面？**
- 确认两端在同一子网、接收端已放行 UDP 22222；
- 若交换机禁用组播，在发送端「设置」中改为广播模式；
- 旧版接收端与新协议不兼容，请统一使用本项目版本。

**在线接收端一直显示 0 台？**
- 教师机未放行 UDP 22223，或学生端为旧版本（旧版不发心跳）；
- 不影响广播本身，只是自动调节不生效。

**macOS 采集失败或画面全黑？**
- 未授予“屏幕录制”权限。到系统设置中授权后重新启动程序。

**画面卡顿？**
- 在设置中降低采集宽度或增大帧间隔；
- 检查交换机端口流量与广播/组播抑制设置。

## 许可

本项目以 **MIT License** 发布。

Copyright (c) 2026 tsingke <tsingke@hotmail.com>

完整条款见仓库根目录的 `LICENSE` 文件。
