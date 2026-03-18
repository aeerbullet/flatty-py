"""
flatty/services/formatter.py
负责格式化输出、Token 估算和文件写入。
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Iterator, Optional, Tuple
import os
import re

from ..config import SEPARATOR_TEMPLATE, DEFAULT_OUTPUT_DIR, AUTO_COPY_TO_CLIPBOARD
from ..exceptions import FormatError
from ..utils.logger import get_logger

logger = get_logger(__name__)

def estimate_tokens_simple(file_path: Path) -> int:
    """简单的 Token 估算：文件大小 / 4"""
    try:
        return file_path.stat().st_size // 4
    except OSError:
        return 0

# 尝试导入 tiktoken 以获得更准确的估算
try:
    import tiktoken
    encoder = tiktoken.get_encoding("cl100k_base") # GPT-4/3.5 使用的编码
    
    def estimate_tokens_accurate(file_path: Path) -> int:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return len(encoder.encode(content))
        except Exception:
            return estimate_tokens_simple(file_path)
            
    ESTIMATE_FUNC = estimate_tokens_accurate
    logger.debug("Using tiktoken for accurate token estimation.")
except ImportError:
    ESTIMATE_FUNC = estimate_tokens_simple
    logger.debug("tiktoken not found. Using simple size-based estimation.")


def get_version_info(project_path: Path) -> Tuple[str, bool]:
    """
    获取版本信息，返回 (version_string, is_dirty)
    
    版本号优先级：
    1. Git 最新的 tag（如果有）
    2. pyproject.toml 中定义的版本（如果存在且无 tag）
    3. Git commit hash（如果存在 git 仓库但无 tag）
    4. 日期版本 dev-YYYYMMDD（兜底）
    
    如果工作区有未提交的修改，添加 dirty 标识
    """
    is_dirty = False
    
    # 检查 Git 状态
    try:
        # 检查是否在 git 仓库中
        subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=project_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        
        # 检查是否有未提交的修改
        try:
            status = subprocess.check_output(
                ['git', 'status', '--porcelain'],
                cwd=project_path,
                text=True
            )
            is_dirty = bool(status.strip())
        except subprocess.CalledProcessError:
            pass
        
        # 尝试获取最新的 tag
        try:
            tag = subprocess.check_output(
                ['git', 'describe', '--tags', '--abbrev=0', '--match', 'v*'],
                cwd=project_path,
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            # 移除 v 前缀（如果有）
            tag = tag.lstrip('v')
            return tag, is_dirty
        except subprocess.CalledProcessError:
            pass
        
        # 没有 tag，获取最新的 commit hash
        try:
            commit_hash = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=project_path,
                text=True
            ).strip()
            return commit_hash, is_dirty
        except subprocess.CalledProcessError:
            pass
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 不是 git 仓库或 git 未安装
        logger.debug("Not a git repository or git not available")
    
    # 尝试从 pyproject.toml 读取版本
    pyproject_path = project_path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text(encoding='utf-8')
            # 简单的正则匹配，避免引入 toml 依赖
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1), is_dirty
        except Exception as e:
            logger.debug(f"Failed to parse pyproject.toml: {e}")
    
    # 尝试从 package.json 读取版本（适用于 JS/TS 项目）
    package_json_path = project_path / "package.json"
    if package_json_path.exists():
        try:
            import json
            data = json.loads(package_json_path.read_text(encoding='utf-8'))
            if "version" in data:
                return data["version"], is_dirty
        except Exception:
            pass
    
    # 兜底：使用日期版本
    return f"dev-{datetime.now().strftime('%Y%m%d')}", is_dirty


def format_version(version: str, is_dirty: bool) -> str:
    """格式化版本字符串"""
    if is_dirty:
        return f"{version}-dirty"
    return version


class RepoFormatter:
    def __init__(self, output_dir: Optional[Path] = None, project_name: Optional[str] = None):
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.project_name = project_name or "project"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_tree(self, files: List[Path], root_path: Path) -> List[str]:
        """生成目录树结构字符串"""
        lines = []
        lines.append("# Complete Repository Structure:")
        lines.append("# (showing all directories and files with token counts)")
        
        # 按目录分组
        dirs_map = {}
        for f in files:
            parent = f.parent
            if parent not in dirs_map:
                dirs_map[parent] = []
            dirs_map[parent].append(f)
        
        # 排序目录
        sorted_dirs = sorted(dirs_map.keys(), key=lambda p: p.parts)
        
        for d in sorted_dirs:
            rel_dir = d.relative_to(root_path)
            depth = len(rel_dir.parts) - 1 if str(rel_dir) != '.' else 0
            indent = "  " * depth
            
            # 计算该目录下文件的总 token
            dir_files = dirs_map[d]
            dir_tokens = sum(ESTIMATE_FUNC(f) for f in dir_files)
            
            if str(rel_dir) == '.':
                lines.append(f"#{indent}./ (~{dir_tokens} tokens)")
            else:
                lines.append(f"#{indent}{rel_dir}/ (~{dir_tokens} tokens)")
            
            # 列出文件
            for f in sorted(dir_files, key=lambda x: x.name):
                tokens = ESTIMATE_FUNC(f)
                lines.append(f"#{indent}  └── {f.name} (~{tokens} tokens)")
                
        lines.append("#")
        return lines

    def _generate_content(self, files: List[Path], root_path: Path) -> List[str]:
        """生成文件内容部分"""
        lines = []
        for f in files:
            try:
                rel_path = str(f.relative_to(root_path))
                lines.append(SEPARATOR_TEMPLATE.format(rel_path))
                content = f.read_text(encoding='utf-8', errors='replace')
                lines.append(content)
                lines.append("") # 空行分隔
            except Exception as e:
                logger.warning(f"Failed to read {f}: {e}")
                lines.append(f"# Error reading file: {e}")
                lines.append("")
        return lines

    def format_and_save(self, files: Iterator[Path], root_path: Path) -> Path:
        """主流程：收集文件，生成内容，保存"""
        logger.info("Formatting output...")
        
        # 将生成器转为列表以便多次遍历 (构建树和写内容)
        # 注意：如果文件极多，这里会消耗内存。对于超大项目可优化为两次扫描或缓存元数据
        valid_files = list(files)
        
        if not valid_files:
            logger.warning("No files matched the criteria. Output will be empty.")
        
        # 获取版本信息
        version_raw, is_dirty = get_version_info(root_path)
        version_str = format_version(version_raw, is_dirty)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_filename = f"{self.project_name}-flat-{version_str}-{timestamp}.txt"
        output_path = self.output_dir / output_filename
        
        all_lines = []
        
        # Header
        all_lines.append(self.project_name)
        all_lines.append(f"Version: {version_str}")
        all_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        all_lines.append("")
        
        # Tree
        all_lines.extend(self._generate_tree(valid_files, root_path))
        all_lines.append("")
        
        # Content
        all_lines.extend(self._generate_content(valid_files, root_path))
        
        # Write
        try:
            content_text = "\n".join(all_lines)
            output_path.write_text(content_text, encoding='utf-8')
            logger.info(f"✅ Output saved to: {output_path}")
            
            # 根据配置决定是否复制到剪贴板
            if AUTO_COPY_TO_CLIPBOARD:
                self._copy_to_clipboard(content_text)
            else:
                logger.debug("Clipboard copying is disabled by configuration.")
            
            # macOS 自动打开 Finder
            if sys.platform == 'darwin':
                try:
                    subprocess.run(['open', '-R', str(output_path)], check=False, capture_output=True)
                except Exception:
                    pass
                    
            return output_path
            
        except Exception as e:
            raise FormatError(f"Failed to write output file: {e}")

    def _copy_to_clipboard(self, text: str):
        """尝试复制文本到剪贴板"""
        try:
            import pyperclip
            # 对于超大文本，pyperclip 可能会失败或阻塞，设置限制或警告
            if len(text) > 10_000_000: # 10MB 限制
                logger.warning("Output too large to copy to clipboard automatically.")
                return
                
            pyperclip.copy(text)
            logger.info("Content copied to clipboard.")
        except ImportError:
            logger.debug("pyperclip not installed. Clipboard copying skipped.")
        except Exception as e:
            logger.warning(f"Failed to copy to clipboard: {e}")