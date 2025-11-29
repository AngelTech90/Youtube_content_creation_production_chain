# AI-Powered Subtitle Generator & Injector

Generate professional subtitles using Google Gemini AI to analyze transcriptions, determine optimal subtitle timing, and inject them into videos with custom fonts.

## Overview

This script automates intelligent subtitle generation:
1. **Analyze** transcription with Gemini AI to identify natural boundaries
2. **Enhance** subtitle quality for readability
3. **Generate** optimal timing based on content importance
4. **Create** SRT subtitle files
5. **Inject** subtitles into videos with professional styling

Perfect for content creators, educators, and video producers who want smart, AI-generated subtitles without manual timing adjustments.

## Features

- 🤖 **Gemini AI Analysis** - Intelligent transcription breakdown
- 📊 **Automatic Timing** - AI calculates reading time and pacing
- 🔤 **Smart Segmentation** - Groups related sentences naturally
- ✂️ **Text Optimization** - Ensures readability (40-60 chars per line)
- 🎨 **Custom Styling** - Font size, colors, borders, backgrounds
- 🔤 **Custom Fonts** - Use any TTF font file
- ⚡ **Optional Enhancement** - Second AI pass for quality improvement
- 💾 **SRT Generation** - Creates standard subtitle files
- 🎬 **FFmpeg Integration** - Embeds subtitles directly into video

## Requirements

### System Requirements
- Python 3.7 or higher
- FFmpeg installed
- Google Gemini API key

### Install FFmpeg

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# macOS
brew install ffmpeg

# Verify
ffmpeg -version
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
   - Click "Get API Key" button
   - Create new API key (free tier available)

2. **Set Environment Variable:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   
   # Make permanent
   echo 'export GEMINI_API_KEY="your_api_key_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

## Installation

```bash
# 1. Verify Python 3.7+
python3 --version

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install FFmpeg
sudo apt install ffmpeg  # or your system's package manager

# 4. Set Gemini API key
export GEMINI_API_KEY="your_api_key_here"

# 5. Test installation
python subtitle_generator.py --help
```

## Usage

### Basic Usage

**Generate subtitles from transcription (with AI enhancement):**
```bash
python subtitle_generator.py transcription.txt video.mp4 -o output.mp4 \
    --font Arial.ttf
```

**Fast mode (skip enhancement):**
```bash
python subtitle_generator.py transcription.txt video.mp4 -o output.mp4 \
    --font Arial.ttf --no-enhance
```

### Professional Styling

**YouTube/Streaming style:**
```bash
python subtitle_generator.py transcription.txt video.mp4 -o output.mp4 \
    --font Arial.ttf \
    --font-size 32 \
    --font-color white \
    --border-width 3 \
    --border-color black \
    --bg-color black \
    --bg-alpha 0.9
```

**Minimal style:**
```bash
python subtitle_generator.py transcription.txt video.mp4 -o output.mp4 \
    --font Arial.ttf \
    --font-size 20 \
    --no-background
```

### Save SRT File

```bash
# Generate both video and standalone SRT
python subtitle_generator.py transcription.txt video.mp4 \
    -o output.mp4 \
    --srt-output subtitles.srt \
    --font Arial.ttf
```

## Command-Line Arguments

```
positional arguments:
  transcription         Transcription file (.txt)
  video                 Input video file

optional arguments:
  -h, --help            Show help message
  -o, --output OUTPUT   Output video file (required)
  --font FONT           Path to custom TTF font file
  --srt-output SRT      Save generated SRT file
  --api-key API_KEY     Gemini API key (or use GEMINI_API_KEY env var)
  --no-enhance          Skip AI enhancement (faster)
  
Styling options:
  --font-size SIZE      Font size in pixels (default: 24)
  --font-color COLOR    Text color (default: white)
  --border-width WIDTH  Border width in pixels (default: 2)
  --border-color COLOR  Border color (default: black)
  --bg-color COLOR      Background color (default: black)
  --bg-alpha ALPHA      Background opacity 0.0-1.0 (default: 0.8)
  --no-background       Disable background box
```

## How Gemini AI Analysis Works

### Step 1: Transcription Analysis
Gemini analyzes your full transcription and:
- Identifies natural sentence and phrase boundaries
- Groups related content together
- Determines optimal subtitle length (40-60 chars)
- Suggests segment importance levels

### Step 2: Enhancement (Optional)
If enabled, Gemini:
- Checks grammar and spelling
- Improves phrasing for readability
- Ensures proper subtitle structure
- Validates timing appropriateness

### Step 3: Timing Generation
Gemini calculates optimal duration based on:
- Word count (180-200 words per minute reading speed)
- Importance level:
  - High: 5-6 seconds
  - Medium: 3-4 seconds
  - Low: 2-3 seconds
- Natural speech pacing

## Python Module Usage

```python
from subtitle_generator import AISubtitleWorkflow

# Initialize with Gemini API
workflow = AISubtitleWorkflow(api_key="your_api_key", font_path="Arial.ttf")

# Process transcription and generate subtitled video
workflow.process(
    transcription_path="transcription.txt",
    video_path="video.mp4",
    output_video_path="output.mp4",
    font_size=28,
    font_color="white",
    enhance=True  # Use AI enhancement
)
```

### Advanced: Step-by-Step

```python
from subtitle_generator import (
    GeminiTranscriptionAnalyzer,
    SubtitleGenerator,
    SubtitleInjector
)

# 1. Analyze transcription
analyzer = GeminiTranscriptionAnalyzer(api_key="your_key")
segments = analyzer.analyze_transcription("transcription.txt")

# 2. Enhance quality
enhanced = analyzer.enhance_subtitles(segments)

# 3. Generate timing
timed = analyzer.generate_timing(enhanced)

# 4. Create SRT
generator = SubtitleGenerator()
generator.generate_srt(timed, "subtitles.srt")

# 5. Inject into video
injector = SubtitleInjector(font_path="Arial.ttf")
injector.inject_subtitles(
    video_path="video.mp4",
    srt_path="subtitles.srt",
    output_path="final.mp4",
    font_size=28
)
```

## Examples

### Example 1: Podcast to Subtitled Video

```bash
# 1. Transcribe podcast (using speech-to-text tool)
# Creates: podcast_transcript.txt

# 2. Generate AI subtitles
python subtitle_generator.py podcast_transcript.txt podcast.mp3 \
    -o podcast_subtitled.mp4 \
    --font Arial.ttf
```

### Example 2: Educational Video

```bash
# Generate readable subtitles for online course
python subtitle_generator.py lecture_notes.txt lecture.mp4 \
    -o lecture_subtitled.mp4 \
    --font "Source Sans Pro.ttf" \
    --font-size 28 \
    --font-color white
```

### Example 3: YouTube Preparation

```bash
# Professional subtitles for YouTube
python subtitle_generator.py video_script.txt raw_video.mp4 \
    -o youtube_ready.mp4 \
    --font Arial.ttf \
    --font-size 32 \
    --font-color white \
    --border-width 3 \
    --border-color black \
    --srt-output youtube_subtitles.srt
```

### Example 4: Fast Processing (No Enhancement)

```bash
# Quick generation without enhancement step
python subtitle_generator.py transcription.txt video.mp4 \
    -o output.mp4 \
    --font Arial.ttf \
    --no-enhance
```

## Understanding AI Output

### Generated JSON Structure

Gemini returns subtitles structured as:

```json
[
  {
    "text": "Subtitle text here",
    "start": 0.0,
    "end": 3.5,
    "duration": 3.5,
    "importance": "high"
  },
  {
    "text": "Next subtitle",
    "start": 3.6,
    "end": 7.2,
    "duration": 3.6,
    "importance": "medium"
  }
]
```

### Importance Levels

- **High (5-6s):** Key information, complex content
- **Medium (3-4s):** Regular dialogue, standard content
- **Low (2-3s):** Filler, acknowledgments

Gemini automatically assigns based on content analysis.

## Font Management

### Using System Fonts

**Find fonts:**
```bash
# Linux
ls /usr/share/fonts/truetype/

# macOS
ls ~/Library/Fonts/
```

**Use font:**
```bash
python subtitle_generator.py transcription.txt video.mp4 -o output.mp4 \
    --font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
```

### Downloading Fonts

**Google Fonts (Recommended):**
1. Visit [fonts.google.com](https://fonts.google.com)
2. Download TTF format
3. Use: `--font /path/to/downloaded/font.ttf`

## Gemini API Pricing

### Free Tier (Generous)
- 60 requests per minute
- 15 requests per second
- No credit card required for free tier
- Perfect for subtitle generation

### Usage Estimate
- 1-hour transcription: ~3 API calls
- Typical batch: 10-20 calls per month
- Well within free tier limits

## Workflow Integration

### Complete Video Production

```bash
#!/bin/bash

# 1. Extract audio
ffmpeg -i raw_video.mp4 -vn audio.mp3

# 2. Transcribe (using speech-to-text)
# Creates: transcription.txt

# 3. Enhance audio
python cleanvoice_enhancer.py "https://url/audio.mp3" -o enhanced_audio.mp3

# 4. Generate AI subtitles
python subtitle_generator.py transcription.txt raw_video.mp4 \
    -o video_with_subtitles.mp4 \
    --font Arial.ttf

# 5. Mix enhanced audio
python mixer.py video_with_subtitles.mp4 enhanced_audio.mp3 \
    -o final_production.mp4
```

## Best Practices

1. **Transcription Quality:**
   - Use accurate transcriptions (AI speech-to-text works well)
   - Clean up obvious errors before processing
   - Include punctuation for better segmentation

2. **Font Selection:**
   - Use sans-serif fonts (Arial, Helvetica, Open Sans)
   - Ensure font supports all characters in transcription
   - Test with short video first

3. **Styling:**
   - White text on black background: best contrast
   - Font size 24-32 pixels: optimal readability
   - Border width 2-3 pixels: professional look

4. **Gemini Usage:**
   - Short transcriptions (< 5min): Fast processing
   - Long transcriptions: May need to process in segments
   - Always review SRT output before final video

5. **Performance:**
   - Use `--no-enhance` for faster processing
   - Enhancement step adds ~30 seconds
   - FFmpeg encoding time depends on video length

## Troubleshooting

### Error: "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your_api_key"
```

### Error: "FFmpeg not found"
```bash
sudo apt install ffmpeg
```

### Error: "Font file not found"
- Use absolute path: `/full/path/to/font.ttf`
- Verify file exists: `ls -la /path/to/font.ttf`

### Gemini API Rate Limit
- Wait a moment and retry
- Use `--no-enhance` to reduce API calls
- Process in smaller batches

### Poor Subtitle Quality
- Review transcription accuracy first
- Try without enhancement: `--no-enhance`
- Manually edit SRT file if needed

## Tips

1. **Review First:** Always check generated SRT before final encoding
2. **Test:** Start with short 1-minute video clips
3. **Segment:** For very long transcriptions, process in parts
4. **Save SRT:** Use `--srt-output` to keep subtitle files
5. **Archive:** Back up all subtitles for future use

## Gemini Free Tier Limits

- Rate: 60 requests/minute, 15 requests/second
- No cost for personal/educational use
- Perfect for content creators
- Enterprise options available if needed

## License

MIT License - Free for personal and commercial use

## Version

Current Version: 1.0.0

## Author

Video Enhancement Pipeline Project

---

**Pro Tip:** Save SRT files with `--srt-output` for easy editing and reuse across multiple videos!
