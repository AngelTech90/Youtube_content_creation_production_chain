# YouTube Shorts Generator

Automatically generate YouTube Shorts from long-form video using Gemini AI to analyze transcriptions and find optimal segments, then automatically split the video using FFmpeg.

## Overview

This script uses Gemini AI to intelligently analyze your video transcription and identify the best segments for YouTube Shorts (15-60 seconds, optimal 30-45 seconds), then automatically extracts those segments from your video and creates standalone MP4 files ready for upload.

Perfect for content creators who want to maximize reach by repurposing long-form videos into engaging Shorts without manual video editing.

## Features

- 🤖 **Gemini AI Analysis** - Intelligently identifies optimal Shorts segments
- ⏱️ **Automatic Timestamps** - AI generates precise start/end times
- 📊 **Segment Scoring** - Evaluates engagement potential (high/medium/low)
- 🎬 **FFmpeg Integration** - Automatically splits video without re-encoding (fast)
- 📱 **Shorts Optimized** - Creates 30-45 second videos (15-60 max)
- 🎯 **Content Typing** - Identifies segment type (tutorial, entertainment, educational, etc.)
- 💾 **Batch Processing** - Creates multiple Shorts from one video
- ⚡ **Fast Processing** - Uses fast FFmpeg preset for quick extraction

## Requirements

### System Requirements
- Python 3.7 or higher
- FFmpeg installed
- Google Gemini API key

### Install System Dependencies

**FFmpeg:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# macOS
brew install ffmpeg

# Verify
ffmpeg -version
ffprobe -version
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install google-generativeai
```

### API Key Setup

1. **Get Gemini API Key:**
   - Visit [https://ai.google.dev/](https://ai.google.dev/)
   - Click "Get API Key"
   - Create new API key

2. **Set Environment Variable:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

## Installation

```bash
# 1. Verify Python 3.7+
python3 --version

# 2. Install FFmpeg
sudo apt install ffmpeg

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set Gemini API key
export GEMINI_API_KEY="your_api_key_here"

# 5. Test
python youtube_shorts_generator.py --help
```

## Usage

### Basic Usage

**Generate Shorts from transcription and video:**
```bash
python youtube_shorts_generator.py transcription.txt video.mp4 -o shorts/
```

This creates multiple MP4 files in the `shorts/` directory, each being a standalone YouTube Short.

### Custom Output Directory

```bash
python youtube_shorts_generator.py transcription.txt video.mp4 -o my_shorts/
```

### With API Key Argument

```bash
python youtube_shorts_generator.py transcription.txt video.mp4 -o shorts/ --api-key YOUR_KEY
```

## Command-Line Arguments

```
positional arguments:
  transcription         Transcription file (transcription.txt)
  video                 Input video file (MP4, MKV, etc.)

optional arguments:
  -h, --help            Show help message
  -o, --output DIR      Output directory (default: shorts/)
  --api-key API_KEY     Google Gemini API key
```

## Output Format

Creates multiple MP4 files in output directory:

```
shorts/
├── short_01_engaging_hook.mp4 (35 seconds)
├── short_02_key_insight.mp4 (42 seconds)
├── short_03_tutorial_tip.mp4 (38 seconds)
├── short_04_funny_moment.mp4 (28 seconds)
└── short_05_motivational.mp4 (45 seconds)
```

Each file is:
- ✅ Ready to upload to YouTube Shorts
- ✅ Properly encoded MP4 format
- ✅ 30-45 seconds optimal length
- ✅ High quality (CRF 23, H.264)
- ✅ AAC audio codec

## How It Works

### Step 1: Transcription Loading
Loads your video transcription text file to understand content structure.

### Step 2: Video Analysis
Gets total video duration and prepares for segment analysis.

### Step 3: Shorts Segment Identification
Gemini AI analyzes transcription to find:
- Self-contained segments
- Natural pause points
- Engaging hooks or punchlines
- Content that works standalone
- Best segments for social sharing

### Step 4: Engagement Scoring
AI evaluates each segment:
- **High:** Best potential for viral engagement
- **Medium:** Good standalone content
- **Low:** Educational but less viral potential

### Step 5: Timestamp Generation
AI generates precise start/end timestamps for each segment:
- Ensures 30-45 second optimal length
- Finds natural audio/visual boundaries
- Avoids cutting mid-sentence
- Confidence level for each timestamp

### Step 6: Video Splitting
FFmpeg extracts each segment as standalone MP4:
- Fast processing (stream copy when possible)
- High quality (CRF 23)
- H.264 video codec
- AAC audio codec

## Python Module Usage

```python
from youtube_shorts_generator import ShortsWorkflow

# Initialize workflow
workflow = ShortsWorkflow(api_key="your_api_key")

# Process video
shorts = workflow.process(
    transcription_path="transcription.txt",
    video_path="video.mp4",
    output_dir="shorts/"
)

print(f"Created {len(shorts)} Shorts!")
```

## Examples

### Example 1: Tutorial Video

```bash
python youtube_shorts_generator.py tutorial_transcript.txt tutorial.mp4 -o shorts/
```

Creates Shorts from different tutorial tips and steps.

### Example 2: Podcast Episode

```bash
python youtube_shorts_generator.py podcast_transcript.txt podcast.mp4 -o podcast_shorts/
```

Extracts engaging moments and key insights from podcast.

### Example 3: Long-Form Content

```bash
python youtube_shorts_generator.py speech_transcript.txt conference_speech.mp4 -o speech_shorts/
```

Creates bite-sized clips from longer presentation or speech.

## Segment Types

Gemini identifies segments as:

- **Tutorial:** Step-by-step instructions, tips, how-tos
- **Entertainment:** Funny moments, engaging stories
- **Educational:** Key insights, explanations, facts
- **Motivational:** Inspiring quotes, success stories
- **Tip:** Quick practical advice
- **Story:** Narrative moments with high engagement potential

## YouTube Shorts Guidelines

### Duration Requirements:
- **Minimum:** 15 seconds
- **Optimal:** 30-45 seconds
- **Maximum:** 60 seconds

### Video Specifications:
- **Resolution:** 1080x1920 (vertical)
- **Format:** MP4 or WebM
- **Codec:** H.264 video, AAC audio
- **Frame Rate:** 24-60 fps

### Content Tips:
- Strong hook in first 3 seconds
- Vertical video format (9:16)
- Text overlays help engagement
- Captions/subtitles recommended
- Music/sound design important

## Integration with Other Modules

### Complete Content Repurposing Pipeline

```bash
# 1. Generate YouTube metadata
python youtube_title_generator.py transcription.txt -o title.txt
python youtube_description_generator.py transcription.txt -o description.txt
python youtube_tags_generator.py transcription.txt -o tags.txt

# 2. Generate Shorts from same video
python youtube_shorts_generator.py transcription.txt video.mp4 -o shorts/

# 3. Upload Shorts to YouTube using metadata
# (Use YouTube API or manual upload with generated title/description)
```

## Processing Performance

### Speed
- **Analysis:** 10-20 seconds
- **Timestamp Generation:** 5-10 seconds
- **Video Splitting:** Depends on video length
  - 10-minute video: ~1-2 minutes
  - 30-minute video: ~3-5 minutes
  - 60-minute video: ~5-10 minutes

### Quality
- **Video Codec:** H.264 (libx264)
- **Preset:** Fast (balances quality and speed)
- **CRF:** 23 (high quality)
- **Audio:** AAC codec, auto bit rate
- **No quality loss:** Uses stream copy when possible

## Troubleshooting

### Error: "FFmpeg not found"
```bash
# Install FFmpeg
sudo apt install ffmpeg

# Verify
ffmpeg -version
ffprobe -version
```

### Error: "Transcription file not found"
- Verify file path is correct
- Use absolute path if needed
- Check file exists: `ls -la transcription.txt`

### Error: "Video file not found"
- Check video path and filename
- Verify video format is supported
- Test video plays: `ffplay video.mp4`

### Error: "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your_api_key"
```

### Shorts are too short or too long
- This is AI-estimated timing
- Review and trim manually if needed
- Transcription quality affects accuracy

### Video splitting fails
- Check video format is supported (MP4, MKV, AVI, etc.)
- Verify FFmpeg is properly installed
- Test with: `ffprobe -v quiet video.mp4`

### API Rate Limit
- Wait and retry
- Reduce processing frequency
- Batch process later

## Best Practices

1. **Quality Transcription:**
   - Accurate speech-to-text conversion
   - Proper punctuation helps AI understand pacing
   - 500+ words recommended for good segments

2. **Video Source:**
   - Good audio quality (clean, no distortion)
   - Consistent lighting/framing
   - Natural pause points in content

3. **After Generation:**
   - Review generated Shorts
   - Add vertical video format (9:16)
   - Add captions/subtitles for engagement
   - Add music or sound design
   - Add text overlays

4. **YouTube Upload:**
   - Use generated title/description/tags
   - Upload as YouTube Shorts (vertical)
   - Schedule posts across week
   - Track performance

## Output Quality

Generated Shorts are:
- ✅ Properly formatted MP4
- ✅ H.264 video codec
- ✅ AAC audio codec
- ✅ Optimized for YouTube
- ✅ High quality (CRF 23)
- ✅ 44.1kHz or 48kHz audio
- ✅ Ready for direct upload

## Storage Requirements

**Example Calculations:**
- Original 10-minute video: ~100-500 MB
- Generated Shorts (6 videos, ~40s each): ~60-300 MB total
- Per Short average: 10-50 MB depending on quality

Shorts use stream copying (no re-encoding) when possible for efficiency.

## License

MIT License - Free for personal and commercial use

## Version

Current Version: 1.0.0

## Author

Video Enhancement Pipeline Project

---

**Pro Tip:** Use high-quality transcriptions and videos with natural pause points for best Shorts extraction!
