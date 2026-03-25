"""
视频解析 Skill 组件

提供统一的视频解析接口，支持多平台视频分享链接和视频ID解析
"""
import os
import tempfile
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import asdict
import re
from pathlib import Path
from parser import (
    parse_video_share_url,
    VideoInfo
)

# 导入视频下载功能
from video_downloader import (
    download_video,
    download_video_with_tempdir,
    DownloadProgress,
    DownloadError,
    InvalidURLError,
    NetworkError,
    DiskFullError,
    PermissionError,
    FileVerificationError,
    DEFAULT_USER_AGENT,
    DEFAULT_TIMEOUT,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY,
)

# 导入视频转录功能
from transcribe import (
    process_video_transcription,
    save_to_markdown,
    extract_audio,
    transcribe_audio,
    create_tmp_dir,
    load_env,
)


class ParseError(Exception):
    """视频解析异常基类"""
    pass


class UnsupportedPlatformError(ParseError):
    """不支持的平台异常"""
    pass


class InvalidParseURLError(ParseError):
    """无效的URL异常（解析用）"""
    pass


class VideoNotFoundError(ParseError):
    """视频未找到异常"""
    pass


def video_info_to_dict(video_info: VideoInfo) -> Dict:
    """
    将 VideoInfo 对象转换为字典格式
    
    Args:
        video_info: VideoInfo 对象
        
    Returns:
        包含视频信息的字典
    """
    result = asdict(video_info)
    # 处理嵌套的 author 和 images 对象
    if video_info.author:
        result['author'] = asdict(video_info.author)
    if video_info.images:
        result['images'] = [asdict(img) for img in video_info.images]
    return result


async def parse_video_by_url(share_url: str) -> Dict:
    """
    根据视频分享链接解析视频信息
    
    Args:
        share_url: 视频分享链接
        
    Returns:
        包含视频信息的字典，格式如下:
        {
            "video_url": "视频无水印链接",
            "cover_url": "视频封面链接",
            "title": "视频标题",
            "music_url": "视频音乐链接",
            "images": [
                {
                    "url": "图集图片链接",
                    "live_photo_url": "LivePhoto视频链接"
                }
            ],
            "author": {
                "uid": "作者ID",
                "name": "作者昵称",
                "avatar": "作者头像链接"
            }
        }
        
    Raises:
        UnsupportedPlatformError: 不支持的平台
        InvalidURLError: 无效的URL
        VideoNotFoundError: 视频未找到
        ParseError: 其他解析错误
    """
    try:
        video_info = await parse_video_share_url(share_url)
        return video_info_to_dict(video_info)
    except ValueError as e:
        error_msg = str(e)
        if "share url" in error_msg and "does not have source config" in error_msg:
            raise UnsupportedPlatformError(f"不支持的视频平台: {share_url}")
        elif "Failed to parse" in error_msg:
            raise InvalidParseURLError(f"无效的视频链接: {error_msg}")
        elif "failed to parse" in error_msg.lower():
            raise VideoNotFoundError(f"视频解析失败: {error_msg}")
        else:
            raise ParseError(f"解析错误: {error_msg}")
    except Exception as e:
        raise ParseError(f"未知错误: {str(e)}")


def parse_video_by_url_sync(share_url: str) -> Dict:
    """
    同步版本：根据视频分享链接解析视频信息
    
    Args:
        share_url: 视频分享链接
        
    Returns:
        包含视频信息的字典
        
    Raises:
        ParseError: 解析错误
    """
    return asyncio.run(parse_video_by_url(share_url))


def parse_video_by_id_sync(source: str, video_id: str) -> Dict:
    """
    同步版本：根据视频ID和平台解析视频信息
    
    Args:
        source: 视频平台名称
        video_id: 视频ID
        
    Returns:
        包含视频信息的字典
        
    Raises:
        ParseError: 解析错误
    """
    return asyncio.run(parse_video_by_id(source, video_id))


def get_supported_platforms() -> List[str]:
    """
    获取支持的平台列表
    
    Returns:
        支持的平台名称列表
    """
    return [
        "douyin",      # 抖音
        "kuaishou",    # 快手
        "pipixia",     # 皮皮虾
        "weibo",       # 微博
        "weishi",      # 微视
        "lvzhou",      # 绿洲
        "zuiyou",      # 最右
        "quanmin",     # 度小视
        "xigua",       # 西瓜
        "lishipin",    # 梨视频
        "pipigaoxiao", # 皮皮搞笑
        "huya",        # 虎牙
        "acfun",       # A站
        "doupai",      # 逗拍
        "meipai",      # 美拍
        "quanminkge",  # 全民K歌
        "sixroom",     # 六间房
        "xinpianchang",# 新片场
        "haokan",      # 好看视频
        "bilibili",    # 哔哩哔哩
        "redbook",     # 小红书
        "twitter",     # Twitter
    ]


async def download_video_to_temp(
    video_url: str,
    prefix: str = "video_",
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    retry_count: int = DEFAULT_RETRY_COUNT,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    verify: bool = True
) -> Dict:
    """
    下载视频到临时目录（异步接口）
    
    Args:
        video_url: 视频下载 URL
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
        包含下载结果的字典:
        {
            "code": 200,
            "msg": "success",
            "data": {
                "temp_dir": "临时目录路径",
                "video_path": "视频文件路径",
                "file_size": 文件大小（字节）
            }
        }
        
    Raises:
        DownloadError: 下载失败时抛出
    """
    try:
        temp_dir, video_path = download_video_with_tempdir(
            url=video_url,
            prefix=prefix,
            timeout=timeout,
            chunk_size=chunk_size,
            retry_count=retry_count,
            retry_delay=retry_delay,
            on_progress=on_progress,
            on_retry=on_retry,
            user_agent=user_agent,
            verify=verify
        )
        
        file_size = video_path.stat().st_size
        
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "temp_dir": str(temp_dir),
                "video_path": str(video_path),
                "file_size": file_size
            }
        }
    except (InvalidURLError, NetworkError, DiskFullError, PermissionError, FileVerificationError) as e:
        return {
            "code": 500,
            "msg": str(e),
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"下载失败: {str(e)}",
            "data": None
        }


async def parse_and_download_video(
    share_url: str,
    prefix: str = "video_",
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    retry_count: int = DEFAULT_RETRY_COUNT,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    verify: bool = True
) -> Dict:
    """
    解析视频分享链接并下载视频到临时目录（异步接口）
    
    Args:
        share_url: 视频分享链接
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
        包含解析和下载结果的字典:
        {
            "code": 200,
            "msg": "success",
            "data": {
                "parse_info": {...},  # 解析结果
                "download_info": {   # 下载结果
                    "temp_dir": "临时目录路径",
                    "video_path": "视频文件路径",
                    "file_size": 文件大小（字节）
                }
            }
        }
    """
    try:
        # 先解析视频
        parse_result = await parse_video_by_url(share_url)
        
        # 检查是否有视频 URL
        video_url = parse_result.get("video_url")
        if not video_url:
            return {
                "code": 400,
                "msg": "未找到视频 URL，可能是图文笔记",
                "data": {
                    "parse_info": parse_result,
                    "download_info": None
                }
            }
        
        # 下载视频
        download_result = await download_video_to_temp(
            video_url=video_url,
            prefix=prefix,
            timeout=timeout,
            chunk_size=chunk_size,
            retry_count=retry_count,
            retry_delay=retry_delay,
            on_progress=on_progress,
            on_retry=on_retry,
            user_agent=user_agent,
            verify=verify
        )
        
        if download_result["code"] != 200:
            return {
                "code": download_result["code"],
                "msg": download_result["msg"],
                "data": {
                    "parse_info": parse_result,
                    "download_info": None
                }
            }
        
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "parse_info": parse_result,
                "download_info": download_result["data"]
            }
        }
        
    except Exception as e:
        return {
            "code": 500,
            "msg": f"处理失败: {str(e)}",
            "data": None
        }


def download_video_to_temp_sync(
    video_url: str,
    prefix: str = "video_",
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    retry_count: int = DEFAULT_RETRY_COUNT,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    verify: bool = True
) -> Dict:
    """
    下载视频到临时目录（同步版本）
    
    Args:
        video_url: 视频下载 URL
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
        包含下载结果的字典
    """
    return asyncio.run(download_video_to_temp(
        video_url=video_url,
        prefix=prefix,
        timeout=timeout,
        chunk_size=chunk_size,
        retry_count=retry_count,
        retry_delay=retry_delay,
        on_progress=on_progress,
        on_retry=on_retry,
        user_agent=user_agent,
        verify=verify
    ))


def parse_and_download_video_sync(
    share_url: str,
    prefix: str = "video_",
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    retry_count: int = DEFAULT_RETRY_COUNT,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    verify: bool = True
) -> Dict:
    """
    解析视频分享链接并下载视频到临时目录（同步版本）
    
    Args:
        share_url: 视频分享链接
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
        包含解析和下载结果的字典
    """
    return asyncio.run(parse_and_download_video(
        share_url=share_url,
        prefix=prefix,
        timeout=timeout,
        chunk_size=chunk_size,
        retry_count=retry_count,
        retry_delay=retry_delay,
        on_progress=on_progress,
        on_retry=on_retry,
        user_agent=user_agent,
        verify=verify
    ))


# 主要导出接口
__all__ = [
    "parse_video_by_url",
    "parse_video_by_url_sync",
    "get_supported_platforms",
    "ParseError",
    "UnsupportedPlatformError",
    "InvalidParseURLError",
    "VideoNotFoundError",
    # 视频下载相关导出
    "download_video_to_temp",
    "download_video_to_temp_sync",
    "parse_and_download_video",
    "parse_and_download_video_sync",
    "DownloadProgress",
    "DownloadError",
    "NetworkError",
    "DiskFullError",
    "PermissionError",
    "FileVerificationError",
    # 视频转录相关导出
    "process_video_transcription",
    "save_to_markdown",
    "extract_audio",
    "transcribe_audio",
    "create_tmp_dir",
    "load_env",
]


# 命令行入口
import argparse
import json
import os
import sys


def load_env(env_path):
    """
    手动读取 .env 文件
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="解析视频链接，支持 20+ 个主流平台。")
    parser.add_argument("--url", help="要解析的视频分享链接")
    parser.add_argument("--list_platforms", action="store_true", help="列出所有支持的平台")
    parser.add_argument("--download", action="store_true", help="下载视频到临时目录")
    parser.add_argument("--prefix", help="临时目录前缀（默认: video_）")
    parser.add_argument("--timeout", type=int, help="下载超时时间（秒，默认: 300）")
    parser.add_argument("--retry", type=int, help="失败重试次数（默认: 3）")
    parser.add_argument("--cleanup", action="store_true", help="下载完成后自动清理临时文件")

    args = parser.parse_args()

    # 列出支持的平台
    if args.list_platforms:
        platforms = get_supported_platforms()
        print("支持的平台列表:")
        for i, platform in enumerate(platforms, 1):
            print(f"  {i}. {platform}")
        sys.exit(0)

    # 根据 URL 解析
    if args.url:
        try:
            url_reg = re.compile(r"http[s]?:\/\/[\w.-]+[\w\/-]*[\w.-]*\??[\w=&:\-\+\%]*[/]*")
            share_url = url_reg.search(args.url).group()
            
            if args.download:
                # 下载视频到临时目录
                import tempfile
                import shutil
                
                # 准备回调函数
                progress_list = []
                retry_list = []
                
                def progress_callback(progress: DownloadProgress):
                    print(f"下载进度: {progress.progress:.1f}% ({progress.downloaded}/{progress.total} 字节, {progress.speed:.1f}KB/s)")
                    progress_list.append(progress)
                
                def retry_callback(attempt: int, error: Exception):
                    print(f"第 {attempt} 次重试，错误: {error}")
                    retry_list.append((attempt, error))
                
                # 解析并下载视频
                result = parse_and_download_video_sync(
                    share_url=share_url,
                    prefix=args.prefix or "video_",
                    timeout=args.timeout or DEFAULT_TIMEOUT,
                    retry_count=args.retry or DEFAULT_RETRY_COUNT,
                    on_progress=progress_callback,
                    on_retry=retry_callback,
                    verify=True
                )
                
                print("\n--- 处理结果 ---")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                # 如果成功且需要清理
                if args.cleanup and result.get("code") == 200:
                    temp_dir = result.get("data", {}).get("download_info", {}).get("temp_dir")
                    if temp_dir and os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        print(f"\n✅ 已清理临时目录: {temp_dir}")
            
            else:
                # 仅解析视频
                result = parse_video_by_url_sync(share_url)
                print("\n--- 解析结果 ---")
                print(json.dumps(result, ensure_ascii=False, indent=2))
        
        except Exception as e:
            print(f"处理失败: {e}")
            sys.exit(1)

    # 没有提供任何参数
    else:
        parser.print_help()
        sys.exit(1)

