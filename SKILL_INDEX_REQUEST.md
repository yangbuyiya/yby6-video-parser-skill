# Skill Indexing Request

**Repository**: `https://github.com/yangbuyiya/yby6-video-parser-skill`  
**Skill Name**: yby6-video-parser-skill
**Installation**: `npx skills add yangbuyiya/yby6-video-parser-skill`  
**License**: MIT  
**Description**: Video parsing and transcription tool that extracts video information from multiple platform sharing links and converts video speech content to text. Supports 20+ mainstream platforms including Douyin, Kuaishou, Bilibili, and more.

**Environment Variables Required**:
- `SILICONFLOW_API_KEY` - Required for video transcription (get from https://siliconflow.cn/)
- `parse_api_url` (optional) - External parsing API endpoint

**Binaries Required**:
- `ffmpeg` - Required for speech transcription (to extract audio from video)

---

## What this skill does

Provides two main skills for video parsing and transcription:

### video-parser-parse
Parse video sharing links and extract detailed video metadata.

- Supports 20+ mainstream video platforms (Douyin, Kuaishou, Bilibili, Xiaohongshu, Weibo, Twitter, etc.)
- Extracts video URL, cover image, title, music URL, author information
- Supports image gallery and LivePhoto content parsing
- Built-in local parser with no external API dependency required
- Provides both synchronous and asynchronous interfaces for batch processing
- Returns structured JSON output with complete video metadata

### video-parser-transcribe
Transcribe video speech content to text with automated workflow.

- Automated process: parse video → download video → extract audio → speech transcription → generate Markdown report
- Uses SiliconFlow API for high-quality speech recognition
- Supports custom ASR models (default: FunAudioLLM/SenseVoiceSmall)
- Generates structured Markdown reports with video info and transcription
- Option to keep or auto-cleanup temporary files
- Flexible input: accepts video URL or pre-parsed JSON result

---

## Skill structure

```
yby6-video-parser/
├── scripts/
│   ├── skill.py              # Video parsing main script
│   ├── transcribe.py         # Speech transcription script
│   └── parser/              # Platform parsers
│       ├── base.py           # Base parser class
│       ├── douyin.py         # Douyin parser
│       ├── kuaishou.py       # Kuaishou parser
│       ├── bilibili.py       # Bilibili parser
│       ├── redbook.py        # Xiaohongshu parser
│       ├── weibo.py          # Weibo parser
│       └── ...              # Other platform parsers (20+ total)
├── demos/                  # Markdown report output directory
├── tmp/                    # Temporary file storage directory
├── .env.example            # Environment configuration example
├── requirements.txt         # Python dependencies
├── SKILL.md               # Agent instructions
├── README.md              # Chinese documentation
└── README_EN.md          # English documentation
```

---

## Requirements

- **Python** ≥ 3.10
- **ffmpeg**: Required for speech transcription (extracts audio from video)
- **SiliconFlow API Key**: Required for speech transcription feature (get from https://siliconflow.cn/)
- **Network access**: Required for video parsing and API calls
- **Python dependencies**:
  - `httpx>=0.28.1`: HTTP client
  - `fake-useragent>=1.5.1`: Random User-Agent generator
  - `requests>=2.28.0`: Video download and API requests

---

## Supported Platforms

| Platform | Identifier | Platform | Identifier |
|----------|------------|----------|------------|
| 抖音 | douyin | 快手 | kuaishou |
| 小红书 | redbook | 哔哩哔哩 | bilibili |
| 微博 | weibo | 皮皮虾 | pipixia |
| 西瓜视频 | xigua | 微视 | weishi |
| 绿洲 | lvzhou | 最右 | zuiyou |
| 度小视 | quanmin | 梨视频 | lishipin |
| 皮皮搞笑 | pipigaoxiao | 虎牙 | huya |
| A站 | acfun | 逗拍 | doupai |
| 美拍 | meipai | 全民K歌 | quanminkge |
| 六间房 | sixroom | 新片场 | xinpianchang |
| 好看视频 | haokan | Twitter | twitter |

---

## Usage Examples

### Video Metadata Parsing

```bash
# List supported platforms
python scripts/skill.py --list_platforms

# Parse by URL
python scripts/skill.py --url "https://v.douyin.com/xxxxxx"
```

### Video Speech Transcription

```bash
# Basic transcription
python scripts/transcribe.py --url "https://v.douyin.com/xxxxxx"

# Specify API Key and model
python scripts/transcribe.py --url "https://www.xiaohongshu.com/explore/xxxx" --api-key sk-your-key --model FunAudioLLM/SenseVoiceSmall

# Keep temporary files
python scripts/transcribe.py --url "https://www.bilibili.com/video/xxxx" --auto_cleanup false
```

### As Module Usage

```python
from scripts.skill import parse_video_by_url_sync, get_supported_platforms

# Parse video
result = parse_video_by_url_sync("https://v.douyin.com/xxxxxx")
print(result)

# Get supported platforms
platforms = get_supported_platforms()
print(f"支持的平台: {', '.join(platforms)}")
```

---

## Output Format

### Video Parsing Result

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

---

## Key Features

- **Multi-Platform Support**: Parse videos from 20+ mainstream platforms
- **Dual Functionality**: Both metadata parsing and speech transcription
- **Batch Processing**: Asynchronous interface for efficient batch operations
- **Flexible Output**: JSON format for parsing, Markdown report for transcription
- **Built-in Parser**: No external API dependency for video parsing
- **Customizable**: Support for custom ASR models and parsing modes
- **Bilingual Documentation**: Comprehensive Chinese and English documentation
- **Open Source**: MIT License, actively maintained

---

## Use Cases

- Extract video metadata for content analysis and data collection
- Generate video transcripts for subtitle creation and content notes
- Batch process multiple videos for content management
- Convert video content to text for SEO and accessibility
- Analyze video content across multiple platforms

---

## Notes

1. This skill is refactored based on the [parse-video-py](https://github.com/wujunwei928/parse-video-py) project
2. Speech transcription requires SiliconFlow API key and is subject to quota limits
3. Recommended to use official app sharing links for better parsing success rate
4. Parsing results may become invalid due to platform policy changes
5. Please comply with the terms of use and copyright regulations of each platform
