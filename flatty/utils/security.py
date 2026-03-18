"""
flatty/utils/security.py
安全校验工具。
"""
import platform
from pathlib import Path
from ..exceptions import SecurityError

def is_root_directory(path: Path) -> bool:
    """
    检查给定路径是否为系统根目录。
    """
    resolved = path.resolve()
    
    if platform.system() == "Windows":
        # Windows 下判断是否为盘符根目录 (如 C:\)
        # 注意：Windows 没有单一的 "/" 根，而是每个驱动器有自己的根
        drive_letter = resolved.drive.upper()
        if drive_letter and str(resolved).upper() == f"{drive_letter}\\":
            return True
        return False
    else:
        # Unix/Linux/macOS 下判断是否为 "/"
        return str(resolved) == "/"

def validate_path_safety(base_path: Path, target_path: Path):
    """
    确保 target_path 解析后仍然在 base_path 内部。
    用于防止 Zip Slip 攻击。
    抛出 SecurityError 如果校验失败。
    """
    try:
        # resolve() 会解析符号链接和相对路径 (../)
        base_resolved = base_path.resolve()
        target_resolved = target_path.resolve()
        
        # 检查 target 是否以 base 开头
        # 注意：在 Windows 上需要处理大小写问题，但 resolve() 通常返回规范路径
        try:
            target_resolved.relative_to(base_resolved)
        except ValueError:
            raise SecurityError(
                f"Security violation: Path '{target_path}' escapes the base directory '{base_path}'"
            )
    except Exception as e:
        if isinstance(e, SecurityError):
            raise
        raise SecurityError(f"Path validation failed: {e}")