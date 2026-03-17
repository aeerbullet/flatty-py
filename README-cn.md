# Flatty-Py 🐍

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-green.svg)](https://pypi.org/project/flatty-py/)

**Flatty-Py** 是一个Python重写版的 [Flatty](https://github.com/mattmireles/Flatty)，能够将任何本地Git仓库或文件夹转换为一个结构清晰的文本文件，特别适合用于向ChatGPT、Claude等大语言模型（LLM）提供代码上下文。并且提供Token统计功能，方便您了解生成的文本文件的Token数量。

像ChatGPT和Claude这样的LLM允许您上传文件，但它们限制了您一次可以上传的文件数量。当你处理有大量文件的大型代码库时，你不能直接将它们上传到LLM。你最终不得不使用RAG（检索增强生成）技术，根据我的经验，这不如将所有内容上传到完整的上下文窗口有效——尤其是当你需要对架构进行推理或了解整个系统时。

## ✨ 为什么选择 Python 重写版？

原项目使用Shell实现，只能在Unix-like系统（如Linux/macOS）上运行。而本Python重写版则无此限制，可在Windows/Linux/macOS上无缝运行。

## 🚀 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/yourusername/flatty-py.git
cd flatty-py
pip install .

# 或者直接使用 pip（发布后）
# pip install flatty-py
```

### 基础用法

在想要"扁平化"的目录下运行：

```bash
flatty
```

这将在 `~/Documents/flatty/` 目录下生成一个包含完整项目结构的文本文件，文件名格式为：`{项目名}-v{版本}-{时间戳}.txt`。

### 高级过滤

**OR 条件匹配**（默认）：包含任意一个模式的文件
```bash
flatty --pattern "useEffect" --pattern "async function" --condition OR
```

**AND 条件匹配**：同时包含所有模式的文件
```bash
flatty --pattern "TODO" --pattern "FIXME" --condition AND
```

## 📖 完整使用指南

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--pattern` | 过滤模式（可多次使用） | `--pattern "class" --pattern "def"` |
| `--condition` | 多模式组合条件：`AND` 或 `OR`（默认：`OR`） | `--condition AND` |

### 输出文件结构

生成的文本文件包含两部分：

1. **目录树结构**（带Token估算）
   ```
   # ./
   #   └── flatty/ (~2345 tokens)
   #     └── core.py (~2167 tokens)
   ```

2. **文件内容**（完整代码）
   ```
   ====================================SEPARATOR==================================
   flatty/core.py
   ====================================SEPARATOR==================================
   import os
   ...
   ```

### 智能过滤规则

系统会自动排除：
- **二进制文件**：图片、音频、视频、编译产物等
- **版本控制目录**：`.git`、`.svn` 等
- **依赖目录**：`node_modules`、`venv`、`__pycache__` 等
- **IDE配置**：`.idea`、`.vscode` 等
- **临时文件**：`*.swp`、`*.log`、`*.tmp` 等
- **包构建目录**：`*.egg-info`、`dist`、`build` 等

## 🎯 应用场景

### 1. **向 LLM 提供代码上下文**
```bash
# 生成整个项目文件，直接粘贴到 ChatGPT
flatty
```

### 2. **代码审查准备**
```bash
# 只提取包含关键逻辑的文件
flatty --pattern "def process" --pattern "class Handler"
```

### 3. **项目文档生成**
```bash
# 提取所有文档和配置文件
flatty --pattern ".md" --pattern ".txt" --pattern "LICENSE"
```

### 4. **查找特定代码模式**
```bash
# 查找同时包含 TODO 和 BUG 的文件
flatty --pattern "TODO" --pattern "BUG" --condition AND
```

## ⚙️ 高级配置

您可以通过修改 `core.py` 中的常量来自定义行为：

```python
# 自定义输出目录
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "flatty"

# 添加需要排除的目录模式
EXCLUDED_DIR_PATTERNS.add('custom_cache')

# 添加需要包含的文本文件扩展名
TEXT_EXTENSIONS.add('.vue')
TEXT_EXTENSIONS.add('.svelte')
```

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出新想法！

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/flatty-py.git
cd flatty-py

# 创建虚拟环境（可选但推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e .
```

## 🙏 致谢

本项目是原始 [Flatty](https://github.com/mattmireles/Flatty) 的 **Python 重写版本**。

*   **原作**: [Flatty](https://github.com/mattmireles/Flatty) 由 [mattmireles](https://github.com/mattmireles) 创建
*   **灵感**: 感谢原作者的杰出工作，启发了这个更跨平台、更易安装的Python版本

## 📄 许可证

本项目基于 **MIT 许可证** 开源。完整许可证内容请查看 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2024 [您的名字] (Python 重写版本)
Copyright (c) [原项目年份] [原作者名] (原始 Flatty 版本)

Permission is hereby granted...
```
---

**Flatty-Py** - 让您的代码更易于被AI理解和处理！⭐ 如果这个项目对您有帮助，欢迎给个Star！ 