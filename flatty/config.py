"""
flatty/config.py
集中管理配置常量、默认值和数据结构。
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Set, List, Optional
import sys

# --- 版本信息 ---
# 动态获取版本，避免硬编码
try:
    from . import __version__ as package_version
except ImportError:
    package_version = "0.0.0-dev"

VERSION = package_version

# --- 路径配置 ---
# 默认输出目录：用户文档目录下的 flatty 文件夹
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "flatty"

# --- 功能开关配置 ---
# 是否自动复制生成的文本到剪贴板
# True: 自动复制 | False: 不自动复制
AUTO_COPY_TO_CLIPBOARD = False  # 默认为 True，保持原有行为

# --- 文件过滤常量 ---
# 需要排除的目录名模式 (支持通配符)
EXCLUDED_DIR_PATTERNS: Set[str] = {
    '.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build',
    '.idea', '.vscode', '.gradle', 'target', 'character',
    '*.egg-info', '*.cache', '__*__',
}

# 已知的文本文件扩展名 (白名单)
TEXT_EXTENSIONS: Set[str] = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.rb', '.php', '.java', '.go',
    '.c', '.cpp', '.h', '.hpp', '.swift', '.m', '.cs', '.sh', '.pl',
    '.html', '.css', '.scss', '.less', '.sass',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.env', '.example',
    '.md', '.txt', '.rst', '.xml', '.sql', '.conf',
    '.gradle', '.properties', '.plist', '.pbxproj',
    '.gitignore', '.dockerignore', '.eslintrc', '.prettierrc',
    'makefile', 'dockerfile', 'license', 'readme' # 注意：文件名匹配通常在逻辑层处理，这里主要存后缀
}

# 需要排除的文件模式 (支持通配符)
EXCLUDED_FILE_PATTERNS: Set[str] = {
    '*.swp', '*.swo', '*.pyc', '*.pyo', '*.o', '*.obj', '*.exe', '*.dll',
    '*.so', '*.dylib', '*.class', '*.jar', '*.war', '*.ear', '*.zip',
    '*.tar', '*.gz', '*.rar', '*.7z', '*.hex', '*.DS_Store', '*.png',
    '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.pdf', '*.mp3', '*.wav', '*.flac',
    '*.ogg', '*.m4a', '*.wma', '*.mp4',
    '*.log', '*.tmp', '*.temp', '*.bak', '*.backup', '*~', '.#*',
    '*.lock', '*.pid', '*.pyc?',
    # README 变体通常通过文件名逻辑排除，或者在这里添加通配符
    'README-*.md', 'README-??-??.md', 
}

# --- 格式化常量 ---
SEPARATOR_TEMPLATE = "=================FILENAME【{}】==================="

# --- 运行时配置数据类 ---
@dataclass
class FlattyConfig:
    """
    运行时配置对象
    """
    # 输入源
    repo_url: Optional[str] = None
    branch: Optional[str] = None
    root_path: Path = field(default_factory=Path.cwd)
    
    # 过滤规则
    patterns: List[str] = field(default_factory=list)
    condition: str = "OR"  # 'AND' or 'OR'
    
    # 输出设置
    output_dir: Path = field(default_factory=lambda: DEFAULT_OUTPUT_DIR)
    project_name: Optional[str] = None
    
    # 安全与控制
    force_root: bool = False
    
    def validate(self):
        """基本配置校验"""
        if self.condition not in ["AND", "OR"]:
            raise ConfigurationError(f"Invalid condition: {self.condition}. Must be 'AND' or 'OR'.")
        
        # 根目录安全检查将在 CLI 或 Service 层结合 force_root 进行