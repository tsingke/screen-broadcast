# 贡献指南

感谢关注本项目。提交改动前请先阅读以下约定。

## 开发环境

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 app_sender.py     # 教师端
python3 app_receiver.py   # 学生端
```

- Python 3.8+
- 仅依赖 Pillow（Tkinter 为标准库）

## 提交规范

- 提交信息使用 `type: subject` 形式，例如 `fix: 修正高 DPI 下的窗口缩放`
- 一个提交只做一件事，避免混合功能与格式化
- 新增或修改协议时，必须同步更新 `screen_broadcast/core.py`、README 的协议章节，并补充单元测试

## 代码风格

- 遵循 PEP 8，使用 4 空格缩进
- 跨平台代码需同时考虑 Windows 与 macOS：屏幕采集、DPI、路径、字体
- 涉及界面的改动，请在两套系统上至少各启动一次

## Pull Request

1. Fork 本仓库并新建分支
2. 确保 `python -m unittest discover -s tests` 全部通过
3. 在 PR 描述中说明改动内容、测试方式与影响范围

## 版权

本项目以 MIT 协议发布，Copyright (c) 2026 tsingke <tsingke@hotmail.com>。
提交代码即表示同意以相同协议分发。
