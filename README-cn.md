# Flatty-Py 🐍

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-green.svg)](https://pypi.org/project/flatty-py/)

**Flatty-Py** 是一个 Python 重写的 [Flatty](https://github.com/mattmireles/Flatty) 工具，可以将任何本地 Git 仓库或文件夹转换为单个结构清晰的文本文件。它特别适合为大型语言模型（如 ChatGPT 和 Claude）提供代码上下文，并提供了 Token 统计功能，帮助你了解生成文本文件的 Token 数量。

ChatGPT 和 Claude 虽然允许上传文件，但限制一次能上传的文件数量。当处理包含数百个文件的大型代码库时，你无法将所有文件都上传给 LLM。最终不得不使用 RAG（检索增强生成）技术，但根据我的经验，这种方式不如将整个代码库放入完整的上下文窗口中有效——尤其是在需要理解架构或把握整个系统的时候。

[English](README.md) | [中文](README-cn.md)

## ✨ 为什么用 Python 重写？

原项目使用 Shell 实现，仅支持 Unix-like 系统（Linux/macOS）。这个 Python 重写版本没有此类限制，可以完美运行在 Windows、Linux 和 macOS 上。

## 🚀 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/yourusername/flatty-py.git
cd flatty-py
pip install .

# 或者通过 pip 安装（发布后）
# pip install flatty-py
```

### 基本用法

在想要"扁平化"的目录中运行：

```bash
flatty
```

这将在 `~/Documents/flatty/` 目录生成一个包含完整项目结构的文本文件。文件命名格式为：`{项目名}-v{版本}-{时间戳}.txt`。

### 高级过滤

**OR 条件**（默认）：匹配任意模式的文件
```bash
flatty --pattern "useEffect" --pattern "async function" --condition OR
```

**AND 条件**：匹配所有模式的文件
```bash
flatty --pattern "TODO" --pattern "FIXME" --condition AND
```

## 📖 完整使用指南

### 命令行参数

| 参数 | 描述 | 示例 |
|------|------|------|
| `--pattern`, `-p` | 过滤模式（可多次使用） | `--pattern "class" --pattern "def"` |
| `--condition`, `-c` | 模式组合条件：`AND` 或 `OR`（默认：`OR`） | `--condition AND` |
| `--repo`, `-r` | 远程 Git 仓库 URL（支持 GitHub、GitLab、Gitee） | `-r https://github.com/user/repo` |
| `--branch`, `-b` | 要克隆的分支或标签 | `-b main` |
| `--force`, `-f` | 强制在根目录执行（危险！） | `--force` |
| `--output-dir`, `-o` | 输出目录 | `-o ~/my-outputs` |

### 输出文件结构

生成的文本文件包含三部分：

1. **文件头信息**（项目名、版本、生成时间）
   ```
   my-project
   Version: 1.0.0
   Generated: 2026-03-19 01:36:17
   ```

2. **目录树结构**（附带 Token 估算）
   ```
   # Complete Repository Structure:
   # ./
   #   └── flatty/ (~2345 tokens)
   #     └── core.py (~2167 tokens)
   ```

3. **文件内容**（完整代码）
   ```
   ==================FILENAME【flatty/core.py】===================
   import os
   ...
   ```

### 智能过滤规则

系统会自动排除：
- **二进制文件**：图片、音频、视频、编译产物等
- **版本控制目录**：`.git`、`.svn` 等
- **依赖目录**：`node_modules`、`venv`、`__pycache__` 等
- **IDE 配置**：`.idea`、`.vscode` 等
- **临时文件**：`*.swp`、`*.log`、`*.tmp` 等
- **构建目录**：`*.egg-info`、`dist`、`build` 等

## 🎯 使用场景

### 1. **为 LLM 提供代码上下文**
```bash
# 生成完整的项目文件，直接粘贴到 ChatGPT
flatty
```

### 2. **代码审查准备**
```bash
# 只提取包含核心逻辑的文件
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

### 5. **处理远程仓库**
```bash
# 直接处理 GitHub 上的项目
flatty -r https://github.com/user/repo -b main
```

## ⚙️ 高级配置

你可以通过修改 `flatty/config.py` 中的常量来自定义行为：

```python
# 自定义输出目录
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "flatty"

# 添加要排除的目录模式
EXCLUDED_DIR_PATTERNS.add('custom_cache')

# 添加要包含的文本文件扩展名
TEXT_EXTENSIONS.add('.vue')
TEXT_EXTENSIONS.add('.svelte')
```

## 🔧 技术特性

- **跨平台支持**：Windows、Linux、macOS 完美运行
- **智能版本检测**：自动从 Git tag、pyproject.toml、package.json 提取版本号
- **准确的 Token 估算**：可选集成 `tiktoken` 进行精确的 Token 计数
- **远程仓库支持**：直接处理 GitHub、GitLab、Gitee 上的项目
- **.gitignore 支持**：自动遵循项目的 .gitignore 规则
- **安全防护**：防止 Zip Slip 攻击，根目录执行警告

## 🤝 贡献指南

欢迎提交贡献、Issue 和功能请求！

1. Fork 项目
2. 创建功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 提交 Pull Request

### 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/yourusername/flatty-py.git
cd flatty-py

# 创建虚拟环境（可选但推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 以开发模式安装
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 安装可选依赖（更准确的 Token 计数）
pip install -e ".[accurate-tokens]"
```

## 📊 项目结构

```
flatty-py/
├── flatty/
│   ├── __init__.py          # 包初始化
│   ├── cli.py                # 命令行入口
│   ├── config.py             # 配置管理
│   ├── exceptions.py         # 自定义异常
│   ├── services/
│   │   ├── downloader.py     # 远程仓库下载
│   │   ├── formatter.py      # 格式化输出
│   │   └── scanner.py        # 文件扫描
│   └── utils/
│       ├── logger.py         # 日志工具
│       └── security.py       # 安全检查
├── pyproject.toml            # 项目配置
├── README.md                 # 说明文档
└── LICENSE                   # 许可证
```

## 🙏 致谢

本项目是对原 [Flatty](https://github.com/mattmireles/Flatty) 的 **Python 重写**。

*   **原项目**：[Flatty](https://github.com/mattmireles/Flatty)，作者 [mattmireles](https://github.com/mattmireles)
*   **灵感**：感谢原作者出色的工作，启发了这个更具跨平台性、更易安装的 Python 版本

## 📄 许可证

本项目采用 **MIT 许可证**开源。详情请参阅 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2026 zhangee (Python 重写版本)
Copyright (c) 2025 mattmireles (原 Flatty 版本)

特此免费授予任何获得本软件及相关文档文件（"软件"）副本的人不受限制地处理本软件的权利，包括但不限于使用、复制、修改、合并、发布、分发、再许可和/或销售软件副本的权利，并允许获得软件的人这样做，但须符合以下条件：

上述版权声明和本许可声明应包含在软件的所有副本或主要部分中。

本软件按"原样"提供，不提供任何形式的明示或暗示保证，包括但不限于适销性、特定用途适用性和非侵权性的保证。在任何情况下，作者或版权持有人均不对任何索赔、损害或其他责任负责，无论是合同诉讼、侵权行为还是其他行为，均由软件或软件的使用或其他交易引起、出自或与之相关。
```

---

**Flatty-Py** - 让你的代码更容易被 AI 理解和处理！如果觉得有用，请在 GitHub 上给这个项目点个 ⭐！