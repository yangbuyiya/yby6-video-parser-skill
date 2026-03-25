---
name: yby6-video-parser
description: 此技能用于解析短视频链接，支持解析抖音、快手、B站等多个主流平台的短视频和图文链接，并能自动提取语音内容转录为文字。适用于需要批量获取视频元数据或将视频内容转为文本的场景时使用此 skill。
---

# 视频解析与转录技能

此技能提供两个核心功能：视频元数据解析和视频语音转录。支持 20+ 个主流视频平台。

## 使用场景

当出现以下场景时，使用此 skill：

- 当用户需要解析图集内容
- 当用户提供视频分享链接，需要提取视频信息（无水印链接、封面、标题、作者等）时
- 需要将视频中的语音内容转换为文字，用于字幕生成、内容笔记时
- 解析图集内容时

## 核心功能

### 功能一：视频元数据解析与下载

使用内置的解析器直接从视频分享链接中提取视频信息，支持将视频下载到本地临时目录。也可下载视频到本地临时目录，无需依赖外部 API。

### 功能二：视频语音转录

通过自动化流程：解析视频 → 下载视频 → 提取音频 → 语音转录 → 生成 Markdown 报告。

## 如何使用

### 环境前置要求

**重要提示**：使用本技能前，请确保满足以下环境要求：

1. **Python 环境**: Python 3.10 或更高版本
2. **ffmpeg 工具（必需）**:
   - **仅视频解析功能**：不需要 ffmpeg
   - **视频语音转录功能**：必须安装 ffmpeg 并添加到系统环境变量

#### ffmpeg 安装方法

**Windows 系统**:
- 访问 https://www.gyan.dev/ffmpeg/builds/ 下载
- 推荐下载：`ffmpeg-git-full.7z` 或 `ffmpeg-release-essentials.zip`
- 解压到固定目录，例如：`C:\ffmpeg`
- 将 `C:\ffmpeg\bin` 添加到系统环境变量 PATH 中
- 验证安装：在命令行运行 `ffmpeg -version`

**macOS 系统**:
```bash
brew install ffmpeg
```

**Linux 系统**:
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS/RHEL
```

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境配置（仅语音转录功能需要）

复制一份项目根目录当中的`.env.example` 为 `.env` 文件：

```env
# SiliconFlow API Key (必填，用于视频转录功能)
# 获取地址: https://siliconflow.cn/
api_key=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 视频转录模型 (可选，默认: FunAudioLLM/SenseVoiceSmall)
# 支持的模型列表: https://docs.siliconflow.cn/api-reference/audio
model=FunAudioLLM/SenseVoiceSmall

# 视频解析 API 地址 (可选，用于转录功能)
# 如果留空或注释掉，则使用项目内置的本地解析器（推荐）
# 如果填写了外部 API 地址，则使用外部 API 进行视频解析
# 示例: parse_api_url=http://ip:8000/video/share/url/parse?url=
parse_api_url=

# SiliconFlow ASR API 地址 (可选，默认: https://api.siliconflow.cn/v1/audio/transcriptions)
siliconflow_api_url=https://api.siliconflow.cn/v1/audio/transcriptions

# 临时文件目录 (可选，默认: 当前项目下的 tmp 目录)
# 可以配置为绝对路径或相对路径，例如: D:\temp 或 ./tmp
# 留空则使用项目根目录下的 tmp 文件夹
temp_dir=

# 是否自动清理临时文件 (可选，默认: false)
# true: 自动删除临时文件（视频和音频）
# false: 保留临时文件在 tmp/目录中
auto_cleanup_temp_files=false

```

## 脚本使用说明

### 脚本一：`scripts/skill.py` - 视频元数据解析

**作用**: 解析视频分享链接，获取视频详细信息。

**运行方式**:

```bash
python scripts/skill.py [选项]
```

**参数说明**:

| 参数                 | 说明                         | 必需  | 默认值              |
| ------------------ | -------------------------- | --- | ----------------- |
| `--url`            | 要解析的视频分享链接                 | 否   | 无                 |
| `--list_platforms` | 列出所有支持的平台                  | 否   | 无                 |
| `--download`       | 下载视频到临时目录                  | 否   | false             |
| `--prefix`         | 临时目录前缀                     | 否   | video_            |
| `--timeout`        | 下载超时时间（秒）                  | 否   | 300               |
| `--retry`          | 失败重试次数                      | 否   | 3                 |
| `--cleanup`        | 下载完成后自动清理临时文件              | 否   | false             |

**常用示例**:

```bash
# 1) 列出支持的平台
python scripts/skill.py --list_platforms

# 2) 通过分享链接解析视频
python scripts/skill.py --url "https://v.douyin.com/xxxxxx"

# 3) 解析并下载视频到临时目录
python scripts/skill.py --url "https://v.douyin.com/xxxxxx" --download

# 4) 解析并下载视频，下载后自动清理临时文件
python scripts/skill.py --url "https://v.douyin.com/xxxxxx" --download --cleanup

# 5) 自定义下载参数（前缀、超时时间、重试次数）
python scripts/skill.py --url "https://v.douyin.com/xxxxxx" --download --prefix my_video --timeout 600 --retry 5
```

**输出格式**:

仅解析模式（不带 `--download` 参数）：

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

解析并下载模式（带 `--download` 参数）：

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
      "file_size": 文件大小（字节）
    }
  }
}
```

### 脚本二：`scripts/transcribe.py` - 视频语音转录

**作用**: 解析视频链接并自动转录语音内容为文字。

**运行方式**:

```bash
python scripts/transcribe.py --url <VIDEO_URL> [选项]
```

**参数说明**:

| 参数                   | 说明                               | 默认值                           |
| -------------------- | -------------------------------- | ----------------------------- |
| `--url`              | **必需**。要解析的视频分享链接                | 无                             |
| `--api_key`          | SiliconFlow API 密钥。未提供则从 .env 读取 | 从 .env 读取                     |
| `--model`            | 语音识别模型名称                         | `FunAudioLLM/SenseVoiceSmall` |
| `--parse_result`     | 已解析的结果 JSON 字符串（可选，跳过解析步骤）       | 无                             |
| `--auto_cleanup`     | 是否自动清理临时文件（true/false）           | 从 .env 读取                     |
| `--use_local_parser` | 是否使用本地解析器（true/false）            | 从 .env 读取                     |

**常用示例**:

```bash
# 1) 基础解析与转录
python scripts/transcribe.py --url "https://v.douyin.com/xxxxxx"

# 2) 指定 API Key 和模型
python scripts/transcribe.py --url "https://www.xiaohongshu.com/explore/xxxx" --api-key sk-your-key --model FunAudioLLM/SenseVoiceSmall

# 3) 保留临时文件
python scripts/transcribe.py --url "https://www.bilibili.com/video/xxxx" --auto_cleanup false
```

**输出**:

- 命令行实时打印 JSON 格式结果
- 自动在 `demos/` 目录下生成结构化的 Markdown 报告

## 技能资源

### 核心脚本

- `scripts/skill.py` - 视频元数据解析脚本
- `scripts/transcribe.py` - 视频语音转录脚本

### 解析器目录

- `scripts/parser/` - 包含 20+ 个平台的解析器实现

### 输出目录

- `demos/` - Markdown 报告输出目录
- `tmp/` - 临时文件存储目录（视频、音频）

## 支持的平台

| 平台   | 标识符         | 平台      | 标识符          |
| ---- | ----------- | ------- | ------------ |
| 抖音   | douyin      | 快手      | kuaishou     |
| 小红书  | redbook     | 哔哩哔哩    | bilibili     |
| 微博   | weibo       | 皮皮虾     | pipixia      |
| 西瓜视频 | xigua       | 微视      | weishi       |
| 绿洲   | lvzhou      | 最右      | zuiyou       |
| 度小视  | quanmin     | 梨视频     | lishipin     |
| 皮皮搞笑 | pipigaoxiao | 虎牙      | huya         |
| A站   | acfun       | 逗拍      | doupai       |
| 美拍   | meipai      | 全民K歌    | quanminkge   |
| 六间房  | sixroom     | 新片场     | xinpianchang |
| 好看视频 | haokan      | Twitter | twitter      |

## 注意事项

1. **环境依赖**: 语音转录功能需要预先安装 `ffmpeg` 并添加到环境变量
2. **网络要求**: 脚本需要访问网络进行视频解析和 API 调用
3. **API 限制**: 语音转录受 SiliconFlow 额度限制
4. **输出路径**: 临时文件默认保存在 `tmp/` 目录，Markdown 报告保存在 `demos/` 目录
5. **解析模式**: 默认使用项目内置的本地解析器，无需配置外部 API

> **本 Skill 基于** **[parse-video-py](https://github.com/wujunwei928/parse-video-py)** **项目重构而来，感谢原作者的贡献。**