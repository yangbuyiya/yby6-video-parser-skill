"""
视频下载模块
提供从 URL 下载视频到临时目录的功能，支持进度回调、重试机制和文件校验
"""
import os
import requests
import tempfile
import mimetypes
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from urllib.parse import urlparse

# 默认配置
DEFAULT_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1"
DEFAULT_TIMEOUT = 300
DEFAULT_CHUNK_SIZE = 8192
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2


def load_env(env_path=".env"):
    """
    读取 .env 文件
    """
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def get_temp_dir():
    """
    获取临时文件目录配置
    如果 .env 中配置了 temp_dir，则使用配置的路径
    否则使用项目根目录下的 tmp 文件夹
    """
    env_vars = load_env(".env")
    temp_dir = env_vars.get("temp_dir", "").strip()
    
    if temp_dir:
        # 如果配置了自定义路径，使用配置的路径
        return Path(temp_dir)
    else:
        # 默认使用项目根目录下的 tmp 文件夹
        script_dir = Path(__file__).parent.parent
        return script_dir / "tmp"


class DownloadError(Exception):
    """下载异常基类"""
    pass


class InvalidURLError(DownloadError):
    """无效 URL 异常"""
    pass


class NetworkError(DownloadError):
    """网络错误异常"""
    pass


class DiskFullError(DownloadError):
    """磁盘空间不足异常"""
    pass


class PermissionError(DownloadError):
    """权限不足异常"""
    pass


class FileVerificationError(DownloadError):
    """文件校验失败异常"""
    pass


class DownloadProgress:
    """下载进度信息"""
    
    def __init__(self, url: str, downloaded: int, total: int, speed: float = 0.0):
        self.url = url
        self.downloaded = downloaded
        self.total = total
        self.speed = speed
        self.progress = (downloaded / total * 100) if total > 0 else 0.0
    
    def __repr__(self):
        return f"DownloadProgress({self.progress:.1f}%, {self.downloaded}/{self.total}, {self.speed:.1f}KB/s)"


def validate_url(url: str) -> None:
    """
    验证 URL 是否有效
    
    Args:
        url: 待验证的 URL
        
    Raises:
        InvalidURLError: URL 无效时抛出
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise InvalidURLError(f"无效的 URL: {url}")
        if result.scheme not in ['http', 'https']:
            raise InvalidURLError(f"不支持的协议: {result.scheme}")
    except Exception as e:
        if isinstance(e, InvalidURLError):
            raise
        raise InvalidURLError(f"URL 解析失败: {e}")


def verify_video_file(file_path: Path, min_size: int = 1024) -> None:
    """
    验证下载的文件是否为有效的视频文件
    
    Args:
        file_path: 文件路径
        min_size: 最小文件大小（字节），默认 1KB
        
    Raises:
        FileVerificationError: 文件校验失败时抛出
        DiskFullError: 磁盘空间不足时抛出
        PermissionError: 权限不足时抛出
    """
    if not file_path.exists():
        raise FileVerificationError(f"文件不存在: {file_path}")
    
    file_size = file_path.stat().st_size
    
    if file_size == 0:
        raise DiskFullError(f"下载的文件为空，可能是磁盘空间不足或下载中断: {file_path}")
    
    if file_size < min_size:
        raise FileVerificationError(f"文件过小 ({file_size} 字节)，可能下载不完整: {file_path}")
    
    # 检查 MIME 类型
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and not mime_type.startswith('video/'):
        raise FileVerificationError(f"文件类型不是视频: {mime_type}")


def download_video(
    url: str,
    output_dir: Optional[Path] = None,
    filename: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    retry_count: int = DEFAULT_RETRY_COUNT,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    verify: bool = True
) -> Path:
    """
    从 URL 下载视频到指定目录
    
    Args:
        url: 视频下载 URL
        output_dir: 输出目录，如果为 None 则使用系统临时目录
        filename: 输出文件名，如果为 None 则自动生成
        timeout: 下载超时时间（秒）
        chunk_size: 下载块大小（字节）
        retry_count: 失败重试次数
        retry_delay: 重试延迟（秒）
        on_progress: 下载进度回调函数
        on_retry: 重试回调函数
        user_agent: HTTP User-Agent
        verify: 是否验证下载文件
        
    Returns:
        下载文件的绝对路径
        
    Raises:
        InvalidURLError: URL 无效
        NetworkError: 网络错误
        DiskFullError: 磁盘空间不足
        PermissionError: 权限不足
        FileVerificationError: 文件校验失败
        DownloadError: 其他下载错误
    """
    import time
    
    # 验证 URL
    validate_url(url)
    
    # 准备输出目录
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="video_download_"))
    else:
        output_dir = Path(output_dir)
    
    # 确保输出目录存在
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        if e.errno == 28:  # No space left on device
            raise DiskFullError(f"磁盘空间不足，无法创建目录: {output_dir}")
        elif e.errno in [13, 30]:  # Permission denied / Read-only file system
            raise PermissionError(f"权限不足，无法创建目录: {output_dir}")
        else:
            raise DownloadError(f"创建输出目录失败: {e}")
    
    # 准备文件名
    if filename is None:
        import uuid
        filename = f"video_{uuid.uuid4().hex}.mp4"
    
    output_path = output_dir / filename
    
    # 下载参数
    headers = {"User-Agent": user_agent}
    last_error = None
    
    # 重试机制
    for attempt in range(retry_count + 1):
        try:
            print(f"正在下载视频: {url} -> {output_path} (尝试 {attempt + 1}/{retry_count + 1})")
            
            # 发起请求
            response = requests.get(url, headers=headers, stream=True, timeout=timeout)
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()
            
            # 写入文件
            try:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 计算下载速度
                            elapsed = time.time() - start_time
                            speed = (downloaded / elapsed / 1024) if elapsed > 0 else 0.0
                            
                            # 进度回调
                            if on_progress:
                                progress = DownloadProgress(url, downloaded, total_size, speed)
                                on_progress(progress)
            except OSError as e:
                # 删除不完整的文件
                if output_path.exists():
                    output_path.unlink()
                
                if e.errno == 28:  # No space left on device
                    raise DiskFullError(f"磁盘空间不足: {e}")
                elif e.errno in [13, 30]:  # Permission denied
                    raise PermissionError(f"权限不足: {e}")
                else:
                    raise DownloadError(f"写入文件失败: {e}")
            
            # 验证文件
            if verify:
                verify_video_file(output_path)
            
            print(f"视频下载完成: {output_path} ({downloaded} 字节)")
            return output_path
            
        except requests.exceptions.RequestException as e:
            last_error = e
            error_msg = f"网络错误: {e}"
            
            # 删除不完整的文件
            if output_path.exists():
                output_path.unlink()
            
            # 触发重试回调
            if on_retry:
                on_retry(attempt + 1, e)
            
            if attempt < retry_count:
                print(f"{error_msg}，{retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                raise NetworkError(f"下载失败，已重试 {retry_count} 次: {e}")
        
        except (DiskFullError, PermissionError, FileVerificationError) as e:
            # 这些错误不需要重试
            if output_path.exists():
                output_path.unlink()
            raise
        
        except Exception as e:
            last_error = e
            error_msg = f"未知错误: {e}"
            
            # 删除不完整的文件
            if output_path.exists():
                output_path.unlink()
            
            # 触发重试回调
            if on_retry:
                on_retry(attempt + 1, e)
            
            if attempt < retry_count:
                print(f"{error_msg}，{retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                raise DownloadError(f"下载失败: {e}")
    
    # 理论上不会到达这里
    raise DownloadError(f"下载失败: {last_error}")


def download_video_with_tempdir(
    url: str,
    prefix: str = "video_",
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    retry_count: int = DEFAULT_RETRY_COUNT,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    verify: bool = True
) -> tuple[Path, Path]:
    """
    从 URL 下载视频到临时目录（自动创建和清理）
    
    Args:
        url: 视频下载 URL
        prefix: 临时目录前缀
        timeout: 下载超时时间（秒）
        chunk_size: 下载块大小（字节）
        retry_count: 失败重试次数
        retry_delay: 重试延迟（秒）
        on_progress: 下载进度回调函数
        on_retry: 重试回调函数
        user_agent: HTTP User-Agent
        verify: 是否验证下载文件
        
    Returns:
        (临时目录路径, 视频文件路径) 的元组
        
    Raises:
        与 download_video 相同的异常
    """
    import uuid
    
    # 获取配置的临时目录
    config_temp_dir = get_temp_dir()
    
    # 创建临时目录
    if config_temp_dir:
        # 使用配置的目录
        temp_dir = config_temp_dir / f"{prefix}{uuid.uuid4().hex}"
        temp_dir.mkdir(parents=True, exist_ok=True)
    else:
        # 使用系统临时目录
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    
    # 生成文件名
    filename = f"video_{uuid.uuid4().hex}.mp4"
    
    # 下载视频
    video_path = download_video(
        url=url,
        output_dir=temp_dir,
        filename=filename,
        timeout=timeout,
        chunk_size=chunk_size,
        retry_count=retry_count,
        retry_delay=retry_delay,
        on_progress=on_progress,
        on_retry=on_retry,
        user_agent=user_agent,
        verify=verify
    )
    
    return temp_dir, video_path


# 导出公共接口
__all__ = [
    "DownloadError",
    "InvalidURLError",
    "NetworkError",
    "DiskFullError",
    "PermissionError",
    "FileVerificationError",
    "DownloadProgress",
    "validate_url",
    "verify_video_file",
    "download_video",
    "download_video_with_tempdir",
    "DEFAULT_USER_AGENT",
    "DEFAULT_TIMEOUT",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_RETRY_COUNT",
    "DEFAULT_RETRY_DELAY",
]
