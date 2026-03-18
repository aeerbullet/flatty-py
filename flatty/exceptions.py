"""
flatty/exceptions.py
自定义异常类，用于区分不同类型的错误。
"""

class FlattyError(Exception):
    """Flatty 所有自定义异常的基类"""
    pass

class ConfigurationError(FlattyError):
    """配置错误或无效参数时抛出"""
    pass

class SecurityError(FlattyError):
    """安全检查失败时抛出 (如：尝试扫描根目录，Zip Slip 攻击)"""
    pass

class DownloadError(FlattyError):
    """仓库下载或解压失败时抛出"""
    pass

class ScanError(FlattyError):
    """文件扫描或过滤过程中发生错误时抛出"""
    pass

class FormatError(FlattyError):
    """格式化输出或写入文件失败时抛出"""
    pass