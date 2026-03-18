"""
flatty/cli.py
命令行入口点。
"""
import argparse
import sys
from pathlib import Path
import shutil

from .config import VERSION, DEFAULT_OUTPUT_DIR, FlattyConfig , AUTO_COPY_TO_CLIPBOARD
from .exceptions import FlattyError, ConfigurationError, SecurityError, DownloadError
from .utils.logger import get_logger
from .utils.security import is_root_directory
from .services.downloader import RepoDownloader
from .services.scanner import FileScanner
from .services.formatter import RepoFormatter

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description=f"Flatty v{VERSION}: Flatten your codebase into a single text file for LLMs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  flatty                          # Flatten current directory
  flatty -r https://github.com/user/repo  # Flatten a remote repo
  flatty --pattern "auth" --condition AND # Only files containing 'auth'
        """
    )
    
    parser.add_argument(
        '--pattern', '-p',
        action='append',
        default=[],
        help='Pattern to filter files (substring in filename or content). Can be used multiple times.'
    )
    parser.add_argument(
        '--condition', '-c',
        choices=['AND', 'OR'],
        default='OR',
        help='Condition for multiple patterns (default: OR).'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force execution even in root directory (DANGEROUS).'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=None,
        help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})'
    )
    
    group = parser.add_argument_group('Remote Repository')
    group.add_argument(
        '-r', '--repo', 
        help='Remote Git repository URL to flatten (GitHub, GitLab, Gitee)'
    )
    group.add_argument(
        '-b', '--branch', 
        help='Branch or tag to clone (default: main/master)'
    )

    return parser.parse_args()

def main():
    args = parse_args()
    
    # 1. 构建配置对象
    config = FlattyConfig(
        repo_url=args.repo,
        branch=args.branch,
        patterns=args.pattern,
        condition=args.condition,
        output_dir=args.output_dir or DEFAULT_OUTPUT_DIR,
        force_root=args.force
    )
    
    try:
        config.validate()
        
        # 2. 根目录安全检查
        if args.repo:
            # 如果是远程仓库，暂时不检查本地 cwd，因为我们会下载到 temp dir
            # 但还是要检查一下输出目录是否安全（可选）
            pass
        else:
            # 本地模式：检查当前工作目录
            if is_root_directory(Path.cwd()) and not args.force:
                logger.error("⚠️  WARNING: You are trying to run flatty in the ROOT directory!")
                logger.error("This will scan your ENTIRE filesystem. Use --force to override.")
                sys.exit(1)
            config.root_path = Path.cwd()

        # 3. 执行流程
        downloader = None
        work_dir = config.root_path
        project_name = work_dir.name if work_dir != Path.cwd() else work_dir.name # 简单处理
        
        if args.repo:
            logger.info(f"Processing remote repository: {args.repo}")
            downloader = RepoDownloader(args.repo, args.branch)
            try:
                work_dir = downloader.download()
                project_name = downloader.project_name
            except Exception as e:
                # 确保下载失败时清理
                if downloader:
                    downloader.cleanup()
                raise e

        try:
            # 扫描
            scanner = FileScanner(work_dir)
            file_iterator = scanner.scan(
                patterns=config.patterns, 
                condition=config.condition
            )
            
            # 格式化与保存
            formatter = RepoFormatter(
                output_dir=config.output_dir,
                project_name=project_name
            )
            
            output_path = formatter.format_and_save(file_iterator, work_dir)
            
            logger.info(f"🎉 Success! File saved to: {output_path}")

            # 4. 自动复制到剪贴板
            if AUTO_COPY_TO_CLIPBOARD:
                formatter.copy_to_clipboard(output_path)
                logger.info("✅ Copied to clipboard.")
            
        finally:
            # 清理临时目录
            if downloader:
                downloader.cleanup()
                
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)
    except SecurityError as e:
        logger.error(f"Security Error: {e}")
        sys.exit(1)
    except DownloadError as e:
        logger.error(f"Download Error: {e}")
        sys.exit(1)
    except FlattyError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("\nOperation cancelled by user.")
        if downloader:
            downloader.cleanup()
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()