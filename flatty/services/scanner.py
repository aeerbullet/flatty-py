"""
flatty/services/scanner.py
负责文件扫描、过滤和 .gitignore 解析。
"""
import fnmatch
from pathlib import Path
from typing import List, Iterator, Set, Optional
import pathspec

from ..config import TEXT_EXTENSIONS, EXCLUDED_DIR_PATTERNS, EXCLUDED_FILE_PATTERNS
from ..exceptions import ScanError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class FileScanner:
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()
        self.gitignore_spec: Optional[pathspec.PathSpec] = None
        self._load_gitignore()

    def _load_gitignore(self):
        """加载根目录下的 .gitignore 文件"""
        gitignore_file = self.root_path / ".gitignore"
        if gitignore_file.exists():
            try:
                with open(gitignore_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                self.gitignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', lines)
                logger.debug(f"Loaded .gitignore with {len(lines)} rules.")
            except Exception as e:
                logger.warning(f"Failed to parse .gitignore: {e}")
        else:
            logger.debug("No .gitignore found in root.")

    def _is_excluded_by_hardcoded(self, path: Path, is_dir: bool) -> bool:
        """检查硬编码的排除规则"""
        name = path.name
        parts = path.parts
        
        # 检查目录排除
        if is_dir:
            for part in parts:
                if part in EXCLUDED_DIR_PATTERNS:
                    return True
                if any(fnmatch.fnmatch(part, p) for p in EXCLUDED_DIR_PATTERNS if '*' in p):
                    return True
        else:
            # 检查文件排除
            if name in EXCLUDED_FILE_PATTERNS:
                return True
            if any(fnmatch.fnmatch(name, p) for p in EXCLUDED_FILE_PATTERNS if '*' in p):
                return True
            
            # 检查父目录是否被排除
            parent = path.parent
            for part in parent.parts:
                 if part in EXCLUDED_DIR_PATTERNS:
                    return True
                 if any(fnmatch.fnmatch(part, p) for p in EXCLUDED_DIR_PATTERNS if '*' in p):
                    return True
        return False

    def _is_text_file(self, file_path: Path) -> bool:
        """判断是否为文本文件"""
        suffix = file_path.suffix.lower()
        name = file_path.name
        
        # 1. 扩展名白名单
        if suffix in TEXT_EXTENSIONS or name.lower() in [t.lower() for t in TEXT_EXTENSIONS if not t.startswith('.')]:
            return True
            
        # 2. 无扩展名或未知扩展名，尝试读取少量字节判断
        # 注意：这里不再重复读取整个文件，仅在必要时做简单二进制检查
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # 简单的启发式检查：如果包含大量空字节，可能是二进制
                if b'\x00' in chunk:
                    return False
                # 尝试解码
                try:
                    chunk.decode('utf-8')
                    return True
                except UnicodeDecodeError:
                    try:
                        chunk.decode('latin-1') # 更宽松的编码
                        return True
                    except:
                        return False
        except IOError:
            return False

    def _matches_user_patterns(self, file_path: Path, patterns: List[str], condition: str) -> bool:
        """检查用户定义的 pattern (文件名或内容)"""
        if not patterns:
            return True

        name = file_path.name
        name_matches = [p for p in patterns if p in name]
        
        # OR 条件优化：如果文件名已匹配，直接返回 True
        if condition == "OR" and name_matches:
            return True

        # 需要检查内容
        content_matches = []
        try:
            # 只读取一次文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for p in patterns:
                if p in content:
                    content_matches.append(p)
        except Exception as e:
            logger.warning(f"Could not read content of {file_path}: {e}")
            # 如果无法读取内容，视为不匹配内容部分
            content_matches = []

        if condition == "OR":
            return bool(name_matches) or bool(content_matches)
        else: # AND
            # 所有 pattern 必须在文件名或内容中出现至少一次
            all_matched = True
            for p in patterns:
                if p not in name and p not in content_matches:
                    all_matched = False
                    break
            return all_matched

    def scan(self, patterns: List[str] = None, condition: str = "OR") -> Iterator[Path]:
        """
        生成器：遍历并 Yield 符合条件的文件路径
        """
        if patterns is None:
            patterns = []
            
        logger.info(f"Scanning directory: {self.root_path}")
        
        count = 0
        skipped = 0
        
        for file_path in self.root_path.rglob('*'):
            if not file_path.is_file():
                continue

            rel_path = file_path.relative_to(self.root_path)
            str_rel_path = str(rel_path)

            # 1. 检查 .gitignore
            if self.gitignore_spec and self.gitignore_spec.match_file(str_rel_path):
                skipped += 1
                continue

            # 2. 检查硬编码排除规则
            if self._is_excluded_by_hardcoded(file_path, is_dir=False):
                skipped += 1
                continue

            # 3. 检查是否为文本文件
            if not self._is_text_file(file_path):
                skipped += 1
                continue

            # 4. 检查用户 Pattern
            if not self._matches_user_patterns(file_path, patterns, condition):
                skipped += 1
                continue

            count += 1
            yield file_path

        logger.info(f"Scan complete. Found {count} files, skipped {skipped}.")