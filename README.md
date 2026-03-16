# Flatty-Py 🐍

A Python rewrite of the original [Flatty](https://github.com/mattmireles/Flatty). 
Transform any local Git repo or folder into a single text file, perfect for feeding into LLMs like ChatGPT or Claude.

## Why Rewrite in Python?
- **Cross-Platform**: Works seamlessly on Windows, Linux, and macOS (no more `.sh` dependency issues).
- **Easier Installation**: Install via `pip` and run from anywhere.
- **Extensible**: Easier to add new filtering logic or output formats.

## Installation

You can install it directly from the source:

```bash
git clone https://github.com/yourusername/flatty-py.git
cd flatty-py
pip install .
```

## Usage

Basic usage (flatten current directory):

```bash
flatty
```

Filter by patterns:

```bash
# Include files containing "useEffect" OR "async function"
flatty --pattern "useEffect" --pattern "async function" --condition OR

# Include files containing both "useEffect" AND "async function"
flatty --pattern "useEffect" --pattern "async function" --condition AND
```

## Features
- **Smart Filtering**: Automatically skips binary files, `node_modules`, `.git`, etc.
- **Token Estimation**: Shows approximate token counts for each file.
- **Git Aware**: Includes current git tag/commit in the output filename.
- **Clipboard Support**: Automatically copies output to clipboard (requires `pyperclip`).

## License
MIT License.
