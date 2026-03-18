# Flatty-Py 🐍

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-green.svg)](https://pypi.org/project/flatty-py/)

**Flatty-Py** is a Python rewrite of [Flatty](https://github.com/mattmireles/Flatty) that transforms any local Git repository or folder into a single, well-structured text file. It's perfect for providing code context to Large Language Models (LLMs) like ChatGPT and Claude, featuring Token statistics to help you understand the token count of the generated text file.

LLMs like ChatGPT and Claude allow you to upload files, but they limit the number of files you can upload at once. When dealing with large codebases containing hundreds of files, you can't simply upload them all to an LLM. You end up having to use RAG (Retrieval-Augmented Generation) techniques, which in my experience, aren't as effective as uploading everything into the full context window—especially when you need to reason about architecture or understand the entire system.

[English](README.md) | [中文](README-cn.md)

## ✨ Why a Python Rewrite?

The original project is implemented in Shell and only runs on Unix-like systems (Linux/macOS). This Python rewrite has no such limitations and works seamlessly on Windows, Linux, and macOS.

## 🚀 Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/yourusername/flatty-py.git
cd flatty-py
pip install .

# Or via pip (once published)
# pip install flatty-py
```

### Basic Usage

Run in the directory you want to "flatten":

```bash
flatty
```

This will generate a text file in `~/Documents/flatty/` with the complete project structure. The filename format is: `{project-name}-v{version}-{timestamp}.txt`.

### Advanced Filtering

**OR condition** (default): Include files matching any pattern
```bash
flatty --pattern "useEffect" --pattern "async function" --condition OR
```

**AND condition**: Include files matching all patterns
```bash
flatty --pattern "TODO" --pattern "FIXME" --condition AND
```

## 📖 Complete Usage Guide

### Command Line Arguments

| Argument | Description | Example |
|------|------|------|
| `--pattern`, `-p` | Filter pattern (can be used multiple times) | `--pattern "class" --pattern "def"` |
| `--condition`, `-c` | Pattern combination condition: `AND` or `OR` (default: `OR`) | `--condition AND` |
| `--repo`, `-r` | Remote Git repository URL (GitHub, GitLab, Gitee) | `-r https://github.com/user/repo` |
| `--branch`, `-b` | Branch or tag to clone | `-b main` |
| `--force`, `-f` | Force execution in root directory (DANGEROUS!) | `--force` |
| `--output-dir`, `-o` | Output directory | `-o ~/my-outputs` |

### Output File Structure

The generated text file contains three parts:

1. **Header Information** (project name, version, generation time)
   ```
   my-project
   Version: 1.0.0
   Generated: 2026-03-19 01:36:17
   ```

2. **Directory Tree Structure** (with token estimates)
   ```
   # Complete Repository Structure:
   # ./
   #   └── flatty/ (~2345 tokens)
   #     └── core.py (~2167 tokens)
   ```

3. **File Contents** (complete code)
   ```
   ==================FILENAME【flatty/core.py】===================
   import os
   ...
   ```

### Smart Filtering Rules

The system automatically excludes:
- **Binary files**: images, audio, video, compiled artifacts, etc.
- **Version control directories**: `.git`, `.svn`, etc.
- **Dependency directories**: `node_modules`, `venv`, `__pycache__`, etc.
- **IDE configurations**: `.idea`, `.vscode`, etc.
- **Temporary files**: `*.swp`, `*.log`, `*.tmp`, etc.
- **Build directories**: `*.egg-info`, `dist`, `build`, etc.

## 🎯 Use Cases

### 1. **Providing Code Context to LLMs**
```bash
# Generate the entire project file and paste directly into ChatGPT
flatty
```

### 2. **Code Review Preparation**
```bash
# Extract only files containing key logic
flatty --pattern "def process" --pattern "class Handler"
```

### 3. **Project Documentation Generation**
```bash
# Extract all documentation and configuration files
flatty --pattern ".md" --pattern ".txt" --pattern "LICENSE"
```

### 4. **Finding Specific Code Patterns**
```bash
# Find files containing both TODO and BUG
flatty --pattern "TODO" --pattern "BUG" --condition AND
```

### 5. **Processing Remote Repositories**
```bash
# Directly process projects from GitHub
flatty -r https://github.com/user/repo -b main
```

## ⚙️ Advanced Configuration

You can customize behavior by modifying constants in `flatty/config.py`:

```python
# Custom output directory
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "flatty"

# Add directory patterns to exclude
EXCLUDED_DIR_PATTERNS.add('custom_cache')

# Add text file extensions to include
TEXT_EXTENSIONS.add('.vue')
TEXT_EXTENSIONS.add('.svelte')
```

## 🔧 Technical Features

- **Cross-platform Support**: Works perfectly on Windows, Linux, and macOS
- **Smart Version Detection**: Automatically extracts version from Git tags, pyproject.toml, package.json
- **Accurate Token Estimation**: Optional integration with `tiktoken` for precise token counting
- **Remote Repository Support**: Directly process projects from GitHub, GitLab, Gitee
- **.gitignore Support**: Automatically respects your project's .gitignore rules
- **Security Protection**: Prevents Zip Slip attacks, root directory execution warnings

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/flatty-py.git
cd flatty-py

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install optional dependencies (for more accurate token counting)
pip install -e ".[accurate-tokens]"
```

## 📊 Project Structure

```
flatty-py/
├── flatty/
│   ├── __init__.py          # Package initialization
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration management
│   ├── exceptions.py         # Custom exceptions
│   ├── services/
│   │   ├── downloader.py     # Remote repository download
│   │   ├── formatter.py      # Output formatting
│   │   └── scanner.py        # File scanning
│   └── utils/
│       ├── logger.py         # Logging utilities
│       └── security.py       # Security checks
├── pyproject.toml            # Project configuration
├── README.md                 # Documentation
└── LICENSE                   # License file
```

## 🙏 Acknowledgements

This project is a **Python rewrite** of the original [Flatty](https://github.com/mattmireles/Flatty).

*   **Original Work**: [Flatty](https://github.com/mattmireles/Flatty) created by [mattmireles](https://github.com/mattmireles)
*   **Inspiration**: Thanks to the original author's excellent work that inspired this more cross-platform, easier-to-install Python version

## 📄 License

This project is open-sourced under the **MIT License**. See the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 zhangee (Python rewrite version)
Copyright (c) 2025 mattmireles (Original Flatty version)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

**Flatty-Py** - Making your code easier for AI to understand and process! ⭐ Star this project on GitHub if you find it helpful!