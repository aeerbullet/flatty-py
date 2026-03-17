import os
import subprocess
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set, Pattern
import fnmatch

# 配置常量
SEPARATOR_TEMPLATE = "=================FILENAME【{}】==================="
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "flatty"

# 需要排除的目录名 - 支持通配符模式
EXCLUDED_DIR_PATTERNS: Set[str] = {
    '.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build', 
    '.idea', '.vscode', '.gradle', 'target', 'character',
    '*.egg-info',  # 匹配所有以 .egg-info 结尾的目录
    '*.cache',      # 匹配所有缓存目录
    '__*__',        # 匹配所有双下划线包裹的目录（如 __pycache__, __MACOSX__ 等）
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

# 需要排除的文件模式 - 支持通配符
EXCLUDED_FILE_PATTERNS: Set[str] = {
    '*.swp', '*.swo', '*.pyc', '*.pyo', '*.o', '*.obj', '*.exe', '*.dll', 
    '*.so', '*.dylib', '*.class', '*.jar', '*.war', '*.ear', '*.zip', 
    '*.tar', '*.gz', '*.rar', '*.7z', '*.hex', '*.DS_Store', '*.png', 
    '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.pdf', '*.mp3', '*.wav', '*.flac',
    '*.ogg', '*.m4a', '*.wma', '*.mp4',
    '*.log',          # 日志文件
    '*.tmp',          # 临时文件
    '*.temp',         # 临时文件
    '*.bak',          # 备份文件
    '*.backup',       # 备份文件
    '*~',             # 编辑器临时文件
    '.#*',            # emacs 临时文件
    '*.lock',         # 锁文件
    '*.pid',          # 进程ID文件
    '*.pyc?',         # 匹配 .pyc 后可能还有字符的情况
    'README-*.md',        # 匹配所有 README-xxx.md
    'README.*.md',        # 另一种写法，匹配 README.zh.md 等
    'README-??.md',       # 匹配两个字符的语言代码，如 README-cn.md
    'README-??-??.md',    # 匹配 README-zh-CN.md
}

def compile_patterns(patterns: Set[str]) -> List[Pattern]:
    """将通配符模式编译为正则表达式"""
    compiled = []
    for pattern in patterns:
        # 将通配符模式转换为正则表达式
        regex_pattern = fnmatch.translate(pattern)
        compiled.append(re.compile(regex_pattern))
    return compiled

# 预编译排除模式
EXCLUDED_DIR_REGEX = compile_patterns(EXCLUDED_DIR_PATTERNS)
EXCLUDED_FILE_REGEX = compile_patterns(EXCLUDED_FILE_PATTERNS)

def should_exclude_path(path: Path, is_dir: bool = False) -> bool:
    """
    检查路径是否应该被排除
    
    Args:
        path: 要检查的路径
        is_dir: 是否是目录（用于明确指定，如果为None则自动判断）
    
    Returns:
        True 表示应该排除，False 表示保留
    """
    if is_dir is None:
        is_dir = path.is_dir()
    
    # 检查路径的每个部分
    for part in path.parts:
        # 对每个部分应用正则匹配
        regex_list = EXCLUDED_DIR_REGEX if is_dir else EXCLUDED_FILE_REGEX
        for pattern_regex in regex_list:
            if pattern_regex.match(part) or pattern_regex.match(str(path)):
                return True
    
    return False

def is_text_file(file_path: Path) -> bool:
    """判断是否为需要处理的文本文件"""
    name = file_path.name
    suffix = file_path.suffix.lower()

    # 1. 检查排除的文件模式（使用正则）
    if should_exclude_path(file_path, is_dir=False):
        return False
    
    # 2. 检查排除的目录（使用正则）
    if should_exclude_path(file_path.parent, is_dir=True):
        return False
    
    # 3. 检查已知文本扩展名或特定文件名
    if suffix in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS:
        return True
    
    # 4. 对于未知扩展名，尝试读取内容判断
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except (UnicodeDecodeError, IOError):
        return False

def get_git_info() -> str:
    """用于获取版本信息用于命名，如果项目存在 git 仓库，则返回 tag-commit_hash-dirty，否则返回 dev-YYYYMMDD-dirty"""
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
    valid_files = []
    for f in all_files:
        if is_text_file(f) and matches_patterns(f, patterns, condition):
            valid_files.append(f)

    # 目录树输出部分保持不变
    dirs = sorted(set([f.parent for f in valid_files]))
    for d in dirs:
        rel_dir = d.relative_to(root_path)
        depth = len(rel_dir.parts) - 1 if str(rel_dir) != '.' else 0
        indent = "  " * depth
        
        dir_tokens = sum(estimate_tokens(f) for f in valid_files if f.parent == d)
        
        if str(rel_dir) == '.':
            lines.append(f"#{indent}./ (~{dir_tokens} tokens)")
        else:
            lines.append(f"#{indent}{rel_dir}/ (~{dir_tokens} tokens)")

        files_in_dir = sorted([f for f in valid_files if f.parent == d])
        for f in files_in_dir:
            tokens = estimate_tokens(f)
            lines.append(f"#{indent}  └── {f.name} (~{tokens} tokens)")

    lines.append("#")

    # 2. File Contents - 使用新的分隔符格式
    for f in valid_files:
        try:
            content = f.read_text(encoding='utf-8')
            # 使用新的分隔符模板，格式为：=================FILENAME【文件路径】===================
            rel_path = str(f.relative_to(root_path))
            lines.append(SEPARATOR_TEMPLATE.format(rel_path))
            lines.append(content)
            lines.append("")  # 空行
        except Exception as e:
            print(f"Warning: Could not read {f}: {e}", file=sys.stderr)

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