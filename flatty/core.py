import os
import subprocess
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set

# 配置常量
SEPARATOR = "====================================SEPARATOR=================================="
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "flatty"

# 需要排除的目录名
EXCLUDED_DIRS: Set[str] = {
    '.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build', 
    '.idea', '.vscode', '.gradle', 'target'
}

# 已知的文本文件扩展名
TEXT_EXTENSIONS: Set[str] = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.rb', '.php', '.java', '.go',
    '.c', '.cpp', '.h', '.hpp', '.swift', '.m', '.cs', '.sh', '.pl',
    '.html', '.css', '.scss', '.less', '.sass',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.env', '.example',
    '.md', '.txt', '.rst', '.xml', '.sql', '.conf',
    '.gradle', '.properties', '.plist', '.pbxproj', 
    '.gitignore', '.dockerignore', '.eslintrc', '.prettierrc',
    'Makefile', 'Dockerfile', 'LICENSE'
}

# 需要排除的文件模式 (使用 fnmatch 或简单检查)
EXCLUDED_FILE_PATTERNS = [
    '*.swp', '*.swo', '*.pyc', '*.pyo', '*.o', '*.obj', '*.exe', '*.dll', 
    '*.so', '*.dylib', '*.class', '*.jar', '*.war', '*.ear', '*.zip', 
    '*.tar', '*.gz', '*.rar', '*.7z', '*.hex', '*.DS_Store', '*.png', 
    '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.pdf'
]

def get_git_info() -> str:
    """用于获取版本信息用于命名， 如果项目存在 git 仓库， 则返回 tag-commit_hash-dirty， 否则返回 dev-YYYYMMDD-dirty"""
    try:
        # Check if inside a git repo
        subprocess.check_call(['git', 'rev-parse', '--is-inside-work-tree'], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"dev-{datetime.now().strftime('%Y%m%d')}"

    try:
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], 
                                      stderr=subprocess.DEVNULL, text=True).strip()
    except subprocess.CalledProcessError:
        tag = ""

    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], 
                                              text=True).strip()
    except subprocess.CalledProcessError:
        commit_hash = "unknown"

    # Check for dirty state
    try:
        status = subprocess.check_output(['git', 'status', '--porcelain'], text=True)
        dirty = "-dirty" if status.strip() else ""
    except subprocess.CalledProcessError:
        dirty = ""

    if tag:
        return f"{tag}-{commit_hash}{dirty}"
    else:
        return f"{commit_hash}{dirty}"

def is_text_file(file_path: Path) -> bool:
    """判断是否为需要处理的文本文件"""
    name = file_path.name
    suffix = file_path.suffix.lower()

    # 1. 检查排除的文件模式
    for pattern in EXCLUDED_FILE_PATTERNS:
        if pattern.startswith('*'):
            if suffix == pattern[1:] or name.endswith(pattern[1:]):
                return False
        elif name == pattern:
            return False
    
    # 2. 检查排除的目录 (path contains)
    for part in file_path.parts:
        if part in EXCLUDED_DIRS:
            return False

    # 3. 检查已知文本扩展名或特定文件名
    if suffix in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS:
        return True
    
    # 4. 对于未知扩展名，尝试读取内容判断 (模拟 file command grep text)
    # 简单方法：尝试解码 utf-8，失败则认为是二进制
    # 为了性能，只读取前几KB
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except (UnicodeDecodeError, IOError):
        return False

def estimate_tokens(file_path: Path) -> int:
    """简单的 Token 估算：文件大小 / 4"""
    try:
        size = file_path.stat().st_size
        return size // 4
    except OSError:
        return 0

def matches_patterns(file_path: Path, patterns: List[str], condition: str) -> bool:
    """检查文件是否匹配指定的模式（内容或文件名）"""
    if not patterns:
        return True

    name_match = any(p in file_path.name for p in patterns)
    
    # 如果文件名已经匹配且条件是 OR，可以直接返回
    if condition == "OR" and name_match:
        return True

    # 检查内容
    content_match = False
    try:
        # 为了性能，这里使用了简单的字符串查找，未使用正则
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            content_match = any(p in content for p in patterns)
    except Exception:
        pass

    if condition == "OR":
        return name_match or content_match
    else:  # AND
        # 必须所有模式都匹配
        for p in patterns:
            in_name = p in file_path.name
            in_content = False
            if not in_name:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        in_content = p in f.read()
                except: pass
            if not (in_name or in_content):
                return False
        return True

def run_flatty(patterns: List[str], condition: str, output_dir: Optional[Path] = None):
    """主执行逻辑"""
    root_path = Path.cwd()
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    version = get_git_info()
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_filename = f"{root_path.name}-v{version}-{timestamp}.txt"
    output_path = output_dir / output_filename

    all_files = sorted([p for p in root_path.rglob('*') if p.is_file()])

    lines = []
    
    # Header
    lines.append(root_path.name)
    lines.append(str(datetime.now()))
    lines.append("")
    lines.append("# Complete Repository Structure:")
    lines.append("# (showing all directories and files with token counts)")

    # Build Structure Tree
    # 为了模拟原版的目录树结构，我们需要先收集所有有效的文件
    valid_files = []
    for f in all_files:
        if is_text_file(f) and matches_patterns(f, patterns, condition):
            valid_files.append(f)

    # 计算目录 token (模拟原版逻辑：遍历目录计算文件总和)
    # 为了简化 Python 实现，我们可以构建一个树状结构
    # 这里为了简单，直接遍历输出
    
    # 1. Directories
    dirs = sorted(set([f.parent for f in valid_files]))
    for d in dirs:
        rel_dir = d.relative_to(root_path)
        depth = len(rel_dir.parts) - 1 if str(rel_dir) != '.' else 0
        indent = "  " * depth
        
        # Calc tokens for this directory
        dir_tokens = sum(estimate_tokens(f) for f in valid_files if f.parent == d)
        
        if str(rel_dir) == '.':
            lines.append(f"#{indent}./ (~{dir_tokens} tokens)")
        else:
            lines.append(f"#{indent}{rel_dir}/ (~{dir_tokens} tokens)")

        # List files in this dir
        files_in_dir = sorted([f for f in valid_files if f.parent == d])
        for f in files_in_dir:
            tokens = estimate_tokens(f)
            lines.append(f"#{indent}  └── {f.name} (~{tokens} tokens)")

    lines.append("#")
    lines.append(SEPARATOR)

    # 2. File Contents
    for f in valid_files:
        try:
            content = f.read_text(encoding='utf-8')
            lines.append(SEPARATOR)
            lines.append(str(f.relative_to(root_path)))
            lines.append(SEPARATOR)
            lines.append(content)
            lines.append("") # newline at end
        except Exception as e:
            print(f"Warning: Could not read {f}: {e}", file=sys.stderr)

    lines.append(SEPARATOR)

    # Write output
    output_path.write_text("\n".join(lines), encoding='utf-8')
    print(f"Processing complete! Output saved to: {output_path}")

    # Clipboard & Finder (Platform specific)
    copied = False
    try:
        import pyperclip
        pyperclip.copy(output_path.read_text(encoding='utf-8'))
        copied = True
        print("Content copied to clipboard.")
    except ImportError:
        print("Hint: Install 'pyperclip' to enable automatic clipboard copying.")
    except Exception as e:
        print(f"Failed to copy to clipboard: {e}")

    # Open in Finder (macOS)
    if sys.platform == 'darwin':
        try:
            subprocess.run(['open', '-R', str(output_path)])
        except: pass
    
    return output_path
