"""
flatty/services/downloader.py
负责 Git 仓库的下载与解压逻辑。
"""
import io
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple
import requests
from urllib.parse import urlparse

from ..config import VERSION
from ..exceptions import DownloadError, SecurityError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class RepoDownloader:
    def __init__(self, repo_url: str, branch: Optional[str] = None):
        self.repo_url = repo_url
        self.branch = branch
        self.temp_dir: Optional[Path] = None
        self.project_name = ""
        self.platform = ""

    def _parse_repo_info(self) -> Tuple[str, str, str, str]:
        """解析 URL 获取平台、所有者、仓库名和默认分支"""
        parsed = urlparse(self.repo_url)
        netloc = parsed.netloc.lower()
        path_parts = [p for p in parsed.path.strip('/').split('/') if p]

        if len(path_parts) < 2:
            raise DownloadError(f"Invalid repository URL format: {self.repo_url}")

        owner = path_parts[0]
        repo_raw = path_parts[1].replace('.git', '')
        
        # 确定平台和默认分支
        if 'github.com' in netloc:
            platform = 'github'
            default_branch = 'main' # 现代 GitHub 默认 main，旧项目可能是 master，这里先假设 main，后续可优化检测
        elif 'gitlab.com' in netloc:
            platform = 'gitlab'
            default_branch = 'main'
        elif 'gitee.com' in netloc:
            platform = 'gitee'
            default_branch = 'master'
        else:
            raise DownloadError(f"Unsupported platform: {netloc}. Supported: GitHub, GitLab, Gitee.")

        return platform, owner, repo_raw, default_branch

    def _get_download_url(self, platform: str, owner: str, repo: str, branch: str) -> str:
        """构建下载 URL"""
        if platform == 'github':
            return f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        elif platform == 'gitlab':
            return f"https://gitlab.com/{owner}/{repo}/-/archive/{branch}/{repo}-{branch}.zip"
        elif platform == 'gitee':
            return f"https://gitee.com/{owner}/{repo}/repository/archive/{branch}.zip"
        raise DownloadError(f"Cannot generate URL for platform: {platform}")

    def download(self) -> Path:
        """执行下载和解压，返回临时根目录路径"""
        logger.info(f"Parsing repository URL: {self.repo_url}")
        platform, owner, repo, default_branch = self._parse_repo_info()
        self.platform = platform
        self.project_name = repo
        
        branch_name = self.branch or default_branch
        download_url = self._get_download_url(platform, owner, repo, branch_name)

        logger.info(f"Downloading {owner}/{repo} ({branch_name}) from {platform}...")
        
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"flatty_{repo}_"))
        
        try:
            # 流式下载
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # 读取内容到内存 (对于超大仓库可能需要优化为直接写磁盘再解压，但 zip 库通常需要文件对象)
            # 这里为了简单保持内存操作，若仓库极大 (>500MB) 建议改用临时文件
            content = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content.write(chunk)
                    downloaded += len(chunk)
                    # 简单的进度日志
                    if total_size and downloaded % (1024 * 1024) == 0:
                        logger.debug(f"Downloaded {downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB")

            content.seek(0)
            
            logger.info("Extracting archive...")
            with zipfile.ZipFile(content) as zip_file:
                # 安全检查：防止 Zip Slip
                for member in zip_file.namelist():
                    target_path = self.temp_dir / member
                    # 确保解析后的绝对路径仍在 temp_dir 内
                    try:
                        target_path.resolve().relative_to(self.temp_dir.resolve())
                    except ValueError:
                        raise SecurityError(f"Zip Slip attempt detected: {member}")

                zip_file.extractall(self.temp_dir)

            # 寻找实际的项目根目录 (通常是 zip 中的第一个文件夹)
            # 结构通常是: temp_dir/repo-name-branch/file...
            subdirs = [d for d in self.temp_dir.iterdir() if d.is_dir()]
            if len(subdirs) == 1:
                self.temp_dir = subdirs[0] # 将根指向实际代码目录
            elif len(subdirs) == 0:
                raise DownloadError("Archive appears to be empty or malformed.")
            else:
                logger.warning(f"Multiple root directories found in archive. Using the first one: {subdirs[0].name}")
                self.temp_dir = subdirs[0]

            normalized_path = self.temp_dir.resolve()
            logger.info(f"✅ Download and extraction complete to: {normalized_path}")
            return normalized_path

        except requests.RequestException as e:
            raise DownloadError(f"Failed to download repository: {e}")
        except zipfile.BadZipFile as e:
            raise DownloadError(f"Invalid zip file received: {e}")
        except Exception as e:
            # 清理临时目录
            if self.temp_dir and self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir)
            raise e

    def cleanup(self):
        """清理临时目录"""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            logger.debug(f"Cleaning up temporary directory: {self.temp_dir}")
            shutil.rmtree(self.temp_dir)