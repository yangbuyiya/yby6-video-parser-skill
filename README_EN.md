# Video Parser Skill

A video parsing and transcription tool that extracts video information from multiple platform sharing links, downloads videos to local storage, and converts video speech content to text.

> **This Skill is refactored based on the [parse-video-py](https://github.com/wujunwei928/parse-video-py) project. Thanks to the original author for their contribution.**

## Core Features

- **Video Metadata Parsing and Downloading**: Supports parsing 20+ mainstream platforms via sharing links or video IDs, and can download videos to local storage
- **Speech Transcription**: Automatically converts video speech content to text
- **Image Gallery Support**: Supports parsing image notes and gallery content
- **Dual Mode Parsing**: Supports both built-in parser and external API modes
- **Batch Processing**: Provides asynchronous interface for batch parsing

## Quick Start

### Prerequisites

**Important Note**: Before using this Skill, please ensure the following requirements are met:

1. **Python Environment**: Python 3.10 or higher
2. **ffmpeg Tool (Required)**:
   - **For video parsing only**: ffmpeg is NOT required
   - **For video speech transcription**: ffmpeg MUST be installed and added to system environment variables

#### ffmpeg Installation Methods

**Windows System**:
- Visit https://www.gyan.dev/ffmpeg/builds/ to download
- Recommended downloads: `ffmpeg-git-full.7z` or `ffmpeg-release-essentials.zip`
- Extract to a fixed directory, e.g., `C:\ffmpeg`
- Add `C:\ffmpeg\bin` to system PATH environment variable
- Verify installation: Run `ffmpeg -version` in command line

**macOS System**:
```bash
brew install ffmpeg
```

**Linux System**:
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS/RHEL
```

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Required for Transcription Only)

Create a `.env` file:

```env
# SiliconFlow API Key (Required, for video transcription feature)
api_key=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Video transcription model (default: FunAudioLLM/SenseVoiceSmall)
model=FunAudioLLM/SenseVoiceSmall
# Temporary file directory (optional, default: tmp directory in current project)
# Can be configured as absolute path or relative path, e.g.: D:\temp or ./tmp
temp_dir=
# Auto cleanup temporary files (true: auto cleanup, false: keep in tmp/ directory)
auto_cleanup_temp_files=false
```

### 3. Use Scripts

#### Video Metadata Parsing

```bash
# List supported platforms
python scripts/skill.py --list_platforms

# Parse by URL
python scripts/skill.py --url "https://v.douyin.com/xxxxxx"

# Parse and download video to temporary directory
python scripts/skill.py --url "https://v.douyin.com/xxxxxx" --download

# Parse and download video, auto cleanup temporary files after download
python scripts/skill.py --url "https://v.douyin.com/xxxxxx" --download --cleanup

# Custom download parameters (prefix, timeout, retry count)
python scripts/skill.py --url "https://v.douyin.com/xxxxxx" --download --prefix my_video --timeout 600 --retry 5
```

#### Video Speech Transcription

```bash
# Basic transcription
python scripts/transcribe.py --url "https://v.douyin.com/xxxxxx"

# Specify API Key and model
python scripts/transcribe.py --url "https://www.xiaohongshu.com/explore/xxxx" --api-key sk-your-key --model FunAudioLLM/SenseVoiceSmall

# Keep temporary files
python scripts/transcribe.py --url "https://www.bilibili.com/video/xxxx" --auto_cleanup false
```

## Command Line Arguments

### `scripts/skill.py`

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `--url` | Video sharing URL to parse | No | None |
| `--list_platforms` | List all supported platforms | No | None |
| `--download` | Download video to temporary directory | No | false |
| `--prefix` | Temporary directory prefix | No | video_ |
| `--timeout` | Download timeout in seconds | No | 300 |
| `--retry` | Retry count on failure | No | 3 |
| `--cleanup` | Auto cleanup temporary files after download | No | false |

### `scripts/transcribe.py`

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--url` | **Required**. Video sharing URL to parse | None |
| `--api_key` | SiliconFlow API key | Read from .env |
| `--model` | Speech recognition model name | `FunAudioLLM/SenseVoiceSmall` |
| `--parse_result` | Parsed result JSON string | None |
| `--auto_cleanup` | Auto cleanup temporary files | Read from .env |
| `--use_local_parser` | Use local parser | Read from .env |

## Supported Platforms

| Platform | Identifier | Platform | Identifier |
|----------|------------|----------|------------|
| Douyin | douyin | Kuaishou | kuaishou |
| Xiaohongshu | redbook | Bilibili | bilibili |
| Weibo | weibo | Pipixia | pipixia |
| Xigua Video | xigua | Weishi | weishi |
| Lvzhou | lvzhou | Zuiyou | zuiyou |
| Quanmin | quanmin | Lishipin | lishipin |
| Pipigaoxiao | pipigaoxiao | Huya | huya |
| Acfun | acfun | Doupai | doupai |
| Meipai | meipai | Quanminkge | quanminkge |
| Sixroom | sixroom | Xinpianchang | xinpianchang |
| Haokan Video | haokan | Twitter | twitter |

## Output Format

### Video Parsing Result

**Parse only mode (without `--download` parameter)**:

```json
{
  "video_url": "https://example.com/video.mp4",
  "cover_url": "https://example.com/cover.jpg",
  "title": "视频标题",
  "music_url": "https://example.com/music.mp3",
  "images": [
    {
      "url": "图片链接",
      "live_photo_url": "LivePhoto链接"
    }
  ],
  "author": {
    "uid": "作者ID",
    "name": "作者昵称",
    "avatar": "https://example.com/avatar.jpg"
  }
}
```

**Parse and download mode (with `--download` parameter)**:

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "parse_info": {
      "video_url": "https://example.com/video.mp4",
      "cover_url": "https://example.com/cover.jpg",
      "title": "视频标题",
      "author": {
        "uid": "作者ID",
        "name": "作者昵称",
        "avatar": "https://example.com/avatar.jpg"
      }
    },
    "download_info": {
      "temp_dir": "临时目录路径",
      "video_path": "视频文件路径",
      "file_size": 文件大小
    }
  }
}
```

### Speech Transcription Result

```json
{
  "parse_info": {
    "code": 200,
    "msg": "success",
    "data": {
      "video_url": "https://example.com/video.mp4",
      "title": "视频标题",
      "author": {
        "name": "作者名称",
        "avatar": "https://example.com/avatar.jpg"
      }
    }
  },
  "transcription": "这是视频中的语音转录文本内容..."
}
```

## Usage as a Module

### Video Parsing

```python
from scripts.skill import parse_video_by_url_sync, get_supported_platforms

# Parse video
result = parse_video_by_url_sync("https://v.douyin.com/xxxxxx")
print(result)

# Get supported platforms
platforms = get_supported_platforms()
print(f"Supported platforms: {', '.join(platforms)}")
```

### Video Downloading

```python
from scripts.skill import parse_and_download_video_sync

# Parse and download video
result = parse_and_download_video_sync(
    share_url="https://v.douyin.com/xxxxxx",
    prefix="video_",
    timeout=300,
    retry_count=3,
    verify=True
)

if result["code"] == 200:
    print(f"Video downloaded to: {result['data']['video_path']}")
    print(f"Temporary directory: {result['data']['temp_dir']}")
    print(f"File size: {result['data']['file_size']} bytes")
```

### Speech Transcription

```python
from scripts.transcribe import process_video_transcription, save_to_markdown

# Video transcription
result = process_video_transcription(
    video_url_to_parse="https://v.douyin.com/xxxxxx",
    api_key="your-siliconflow-api-key",
    model="FunAudioLLM/SenseVoiceSmall",
    auto_cleanup=False  # Keep temporary files
)

# Save as Markdown
md_file = save_to_markdown(result, "https://v.douyin.com/xxxxxx")
print(f"Markdown file saved: {md_file}")
```

### Asynchronous Batch Processing

```python
import asyncio
from scripts.skill import parse_video_by_url

async def parse_videos():
    urls = [
        "https://v.douyin.com/xxxxxx",
        "https://v.kuaishou.com/yyyyyy",
        "https://www.xiaohongshu.com/explore/zzzzzz"
    ]
    
    results = await asyncio.gather(*[
        parse_video_by_url(url) for url in urls
    ])
    
    for url, result in zip(urls, results):
        print(f"{url}: {result}")

asyncio.run(parse_videos())
```

## Directory Structure

```
yby6-video-parser/
├── scripts/
│   ├── skill.py              # Video parsing main script
│   ├── transcribe.py         # Speech transcription script
│   └── parser/              # Platform parsers
│       ├── base.py           # Base class
│       ├── douyin.py         # Douyin parser
│       ├── kuaishou.py       # Kuaishou parser
│       └── ...              # Other platform parsers
├── demos/                  # Markdown report output directory
├── tmp/                    # Temporary file storage directory
├── .env.example            # Environment configuration example
├── .env                   # Environment configuration file (create yourself)
├── requirements.txt         # Python dependencies
└── test.py                # Test script
```

## Dependencies

- `httpx>=0.28.1`: HTTP client
- `fake-useragent>=1.5.1`: Random User-Agent generator
- `requests>=2.28.0`: Video download and API requests

## Environment Requirements

- **Python**: 3.10+
- **ffmpeg**: Required for speech transcription (used to extract audio from video)

## Important Notes

1. **Network Requirement**: Requires internet connection to work properly
2. **ffmpeg Dependency**: Speech transcription requires ffmpeg installed and added to environment variables
3. **API Limitations**: Speech transcription is subject to SiliconFlow quota limits
4. **Link Format**: It's recommended to use links shared by official apps
5. **Platform Changes**: Parsing results may become invalid due to platform policy changes
6. **Usage Compliance**: Please comply with the terms of use and copyright regulations of each platform

## FAQ

### Q: What should I do if parsing fails?

A: Possible reasons:
- Platform updated page structure or API
- Video has been deleted or set to private
- Link format is incorrect

It's recommended to try using links shared by the official app.

### Q: How to parse multiple videos in batch?

A: Use asynchronous interface for better efficiency (refer to the "Asynchronous Batch Processing" example above).

### Q: Where are temporary files saved?

A: Temporary files are saved in the `tmp/视频标题` directory by default, and can be kept via the `--auto_cleanup false` parameter.

### Q: How long does speech transcription take?

A: Depends on video duration and network speed, usually 1 minute video takes 2-3 minutes.

## Development Guide

To add support for new platforms:

1. Create a new parser file in the `scripts/parser/` directory
2. Inherit from `BaseParser` class and implement `parse_share_url` and `parse_video_id` methods
3. Register the new platform in `scripts/parser/__init__.py`
4. Add the new platform in the `get_supported_platforms` function in `scripts/skill.py`

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!
