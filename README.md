# 📖 爱看小说 (Bobo Novel Reader)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

**爱看小说** 是一款基于 PyQt6 开发的极致简约、高性能的本地小说阅读器。它不仅支持秒开超大文本文件，还内置了强大的在线搜索与自动下载功能，旨在为小说爱好者提供最纯净的阅读体验。

---

## ✨ 核心功能

### 🚀 极致性能
- **秒开大文件**: 采用流式扫描与二进制解析技术，即使是几百 MB 的《蛊真人》等超长篇小说，也能实现 0.1 秒瞬间开启。
- **智能索引**: 首次加载后自动生成本地目录缓存，再次打开无需重新解析。

### 🔍 在线搜索与下载
- **全网搜书**: 内置多线程爬虫模块，支持直接搜索书名并从主流镜像站抓取内容。
- **纯净下载**: 自动过滤网页广告、干扰链接及冗余排版，一键生成规范的 TXT 电子书。
- **自动入库**: 下载完成后自动合并章节、添加到书架并记忆阅读位置。

### 🎨 沉浸式阅读体验
- **精美排版**: 支持自定义字体大小、行间距、背景主题（护眼/夜间模式）。
- **沉浸模式**: 支持 `F11` 一键全屏，侧边栏可折叠，配合隐藏式控件，打造极致纯净的视野。
- **进度同步**: 自动记录每本书的阅读章节，下次打开精准还原。
- **快捷跳转**: 支持输入章节数快速跳转，配合键盘方向键轻松翻页。

---

## 🛠️ 本地安装

如果你是开发者，可以通过以下步骤在本地环境运行：

### 1. 克隆仓库
```bash
git clone https://github.com/xdcrazyboy/bobo_novel_reader.git
cd bobo_novel_reader
```

### 2. 安装依赖
建议使用虚拟环境：
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

### 3. 运行程序
```bash
python reader_gui.py
```

---

## 📦 开箱即用 (便携版)

对于普通用户，我们提供了编译好的独立 EXE 程序，无需安装 Python 环境即可使用：

1. 进入 `dist/` 目录。
2. 双击运行 `极简小说阅读器.exe`。
3. 所有的配置和缓存都会保存在程序同级目录下，实现真正的“绿色便携”。

---

## ⌨️ 快捷键说明

| 快捷键 | 功能 |
| :--- | :--- |
| **F11** | 切换全屏模式 |
| **Esc** | 退出全屏 |
| **Left / Right** | 上一章 / 下一章 |
| **Up / Down** | 页面微滚动 |

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 协议开源。

---

## 🙌 致谢

感谢所有开源社区的支持，特别感谢 [PyQt6](https://www.riverbankcomputing.com/) 提供的强大 UI 框架。

---
❤️ 如果这个项目对你有帮助，欢迎点个 **Star**！
