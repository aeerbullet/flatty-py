import subprocess
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set, Pattern
import fnmatch
import platform
import tempfile
import re
from urllib.parse import urlparse
import requests
import zipfile
import io

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
    'README.md', 
    'README-*.md',        # 匹配所有 README-xxx.md
    'README.*.md',        # 另一种写法，匹配 README.zh.md 等
    'README-??.md',       # 匹配两个字符的语言代码，如 README-cn.md
    'README-??-??.md',    # 匹配 README-zh-CN.md
}

def extract_repo_name(repo_url: str) -> str:
    """
    从仓库 URL 中提取项目名
    支持格式：
    - https://github.com/username/repo.git
    - https://github.com/username/repo
    - git@github.com:username/repo.git
    - https://gitlab.com/username/repo
    - https://gitee.com/username/repo
    """
    # 移除 .git 后缀
    repo_url = repo_url.rstrip('.git')
    
    # 处理 HTTPS/HTTP 格式
    if '://' in repo_url:
        path_parts = repo_url.split('/')
        return path_parts[-1]
    
    # 处理 SSH 格式 (git@github.com:username/repo)
    elif ':' in repo_url:
        path_part = repo_url.split(':')[-1]
        return path_part.split('/')[-1]
    
    # 如果是本地路径
    else:
        return Path(repo_url).name

def parse_repo_url(repo_url: str) -> tuple:
    """
    解析仓库 URL，返回 (platform, owner, repo, branch)
    """
    parsed = urlparse(repo_url)
    
    # GitHub
    if 'github.com' in parsed.netloc:
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1].replace('.git', '')
            return ('github', owner, repo, 'main')
    
    # GitLab
    elif 'gitlab.com' in parsed.netloc:
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1].replace('.git', '')
            return ('gitlab', owner, repo, 'main')
    
    # Gitee
    elif 'gitee.com' in parsed.netloc:
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1].replace('.git', '')
            return ('gitee', owner, repo, 'master')
    
    return None, None, None, None

def get_download_url(platform: str, owner: str, repo: str, branch: str) -> str:
    """
    根据不同平台生成下载 URL
    """
    if platform == 'github':
        return f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    elif platform == 'gitlab':
        return f"https://gitlab.com/{owner}/{repo}/-/archive/{branch}/{repo}-{branch}.zip"
    elif platform == 'gitee':
        return f"https://gitee.com/{owner}/{repo}/repository/archive/{branch}.zip"
    else:
        return None

def download_and_flattey(repo_url: str, branch: Optional[str], patterns: List[str], condition: str):
    """
    通过平台 CDN 下载仓库压缩包
    """
    # 解析仓库信息
    platform, owner, repo, default_branch = parse_repo_url(repo_url)
    if not platform:
        print(f"Unsupported or invalid repository URL: {repo_url}", file=sys.stderr)
        print("Currently supported: GitHub, GitLab, Gitee", file=sys.stderr)
        sys.exit(1)
    
    branch_name = branch or default_branch
    download_url = get_download_url(platform, owner, repo, branch_name)
    
    if not download_url:
        print(f"Could not generate download URL for {platform}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Downloading {owner}/{repo} ({branch_name}) from {platform}...")
    
    with tempfile.TemporaryDirectory(prefix="flatty_") as tmpdir:
        tmp_path = Path(tmpdir)
        
        try:
            # 下载压缩包
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 解压处理
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                # 获取根目录名（不同平台格式可能不同）
                first_item = zip_file.namelist()[0]
                root_dir = first_item.split('/')[0]
                
                # 解压所有文件，去除根目录
                for file_info in zip_file.infolist():
                    if file_info.is_dir():
                        continue
                    
                    # 计算相对路径
                    rel_path = '/'.join(file_info.filename.split('/')[1:])
                    if not rel_path:
                        continue
                    
                    target_path = tmp_path / rel_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zip_file.open(file_info) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
            
            print(f"✅ Download and extraction complete!")
            
        except requests.RequestException as e:
            print(f"❌ Error downloading repository: {e}", file=sys.stderr)
            if branch and branch != default_branch:
                print(f"  Branch '{branch}' might not exist", file=sys.stderr)
            sys.exit(1)
        except zipfile.BadZipFile as e:
            print(f"❌ Error extracting zip file: {e}", file=sys.stderr)
            sys.exit(1)
        
        # 从 URL 提取项目名
        project_name = extract_repo_name(repo_url)
        
        # 扁平化处理，传入项目名
        run_flatty(
            patterns=patterns, 
            condition=condition, 
            root_path=tmp_path,
            project_name=project_name
        )


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

def is_root_directory() -> bool:
    """
    Check if the current working directory is a system root directory.
    
    Returns:
        True if in root directory (e.g., / on Unix, C: on Windows), 
        False otherwise
    """
    current_path = Path.cwd()
    
    # Get the root directory based on platform
    if platform.system() == "Windows":
        # On Windows, root is like C:\, D:\, etc.
        root_drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        return str(current_path).upper() in [d.upper() for d in root_drives]
    else:
        # On Unix-like systems (Linux, macOS), root is "/"
        return str(current_path) == "/"

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

def run_flatty(patterns: List[str], condition: str,
                root_path: Optional[Path] = None,
                output_dir: Optional[Path] = None,
                project_name: Optional[str] = None):  # 新增参数
    """主执行逻辑"""
    root_path = root_path or Path.cwd()
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 使用传入的项目名，如果没有则使用目录名
    name_for_filename = project_name or root_path.name
    
    version = get_git_info()
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_filename = f"{name_for_filename}-v{version}-{timestamp}.txt"
    output_path = output_dir / output_filename

    all_files = sorted([p for p in root_path.rglob('*') if p.is_file()])

    lines = []
    
    # Header - 使用项目名而不是 root_path.name
    lines.append(name_for_filename)  # 修改这里
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