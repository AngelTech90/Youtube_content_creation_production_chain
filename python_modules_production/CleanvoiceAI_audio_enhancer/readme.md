# CleanVoice Audio Enhancer

Professional AI audio enhancement using CleanVoice API v2. Remove background noise, filler words, mouth sounds, and improve audio quality for podcasts, interviews, and voice content.

## Overview

This script uses CleanVoice's powerful AI engine to automatically enhance audio quality. It intelligently removes background noise, detects and removes filler sounds (um, uh, like), reduces silence, and optimizes overall audio quality. Perfect for podcasters, content creators, and anyone needing professional audio enhancement.

## ⚠️ Important: Public URLs Required

**CleanVoice API requires publicly accessible URLs.** You cannot upload local files directly. Your audio files must be hosted on publicly accessible storage:

- ✅ AWS S3
- ✅ Google Cloud Storage
- ✅ Azure Blob Storage
- ✅ DigitalOcean Spaces
- ✅ Any publicly accessible URL

This allows CleanVoice servers to download and process your files.

## Why CleanVoice?

✅ **Real, Working API** - Documented v2 REST API
✅ **Very Low Cost** - Pay only for what you use
✅ **AI-Powered** - Machine learning for intelligent enhancement
✅ **Multiple Features** - Noise removal, filler words, silence reduction, studio sound
✅ **Fast Processing** - Most files process in minutes
✅ **7-Day Storage** - Files stored temporarily, auto-deleted for privacy

## Features

- 🎵 **Single File Enhancement** - Process one audio file at a time
- 📦 **Batch Processing** - Process multiple files to a directory
- 🔇 **AI Noise Reduction** - Intelligently remove background noise
- 🗣️ **Filler Word Removal** - Detect and remove um, uh, like, etc.
- ⏸️ **Silence Reduction** - Automatically shorten long pauses
- 🎤 **Mouth Sound Removal** - Remove clicks, pops, breathing sounds
- 🎙️ **Breath Control** - Natural reduction or full mute
- 📊 **Studio Sound** - Professional audio processing
- 📊 **Audio Optimization** - Enhance clarity and normalize levels
- ⚡ **Fast Processing** - Most files process in minutes
- 💰 **Pay-Per-Use** - Only pay for what you process

## Requirements

### System Requirements
- Python 3.7 or higher
- Internet connection
- CleanVoice API key

### Python Dependencies
```bash
pip install requests
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

### API Key Setup

1. **Create CleanVoice Account:**
   - Visit [https://app.cleanvoice.ai](https://app.cleanvoice.ai)
   - Sign up for free account

2. **Get API Key:**
   - Log in to dashboard
   - Go to Settings → API Keys
   - Create new API key
   - Copy your API key

3. **Set Environment Variable:**
   ```bash
   # Linux/Mac
   export CLEANVOICE_API_KEY="your_api_key_here"
   
   # Make it permanent
   echo 'export CLEANVOICE_API_KEY="your_api_key_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

## Installation

```bash
# 1. Verify Python 3.7+
python3 --version

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
export CLEANVOICE_API_KEY="your_api_key_here"

# 4. Test installation
python cleanvoice_enhancer.py --help
```

## File Upload: Getting Public URLs

Before using this script, you must upload your audio files to public storage and get their URLs.

### Option 1: AWS S3

```bash
# Upload to S3
aws s3 cp audio.mp3 s3://your-bucket/audio.mp3 --acl public-read

# Get public URL
https://your-bucket.s3.amazonaws.com/audio.mp3
```

### Option 2: Google Cloud Storage

```bash
# Upload to GCS
gsutil cp audio.mp3 gs://your-bucket/audio.mp3

# Make public
gsutil acl ch -u AllUsers:R gs://your-bucket/audio.mp3

# Get public URL
https://storage.googleapis.com/your-bucket/audio.mp3
```

### Option 3: Simple HTTP Server (Testing Only)

```bash
# Start local server (for testing)
python3 -m http.server 8000

# Access at: http://localhost:8000/audio.mp3
# (Only works if accessible from internet)
```

## Usage

### Basic Usage

**Single File:**
```bash
python cleanvoice_enhancer.py "https://example.com/audio.mp3" -o output.mp3
```

**Multiple Files:**
```bash
python cleanvoice_enhancer.py \
  "https://example.com/file1.mp3" \
  "https://example.com/file2.mp3" \
  -o enhanced/
```

### Enhancement Options

**Default Enhancement (Recommended):**
```bash
# Removes noise, normalizes, applies studio sound
python cleanvoice_enhancer.py "https://example.com/audio.mp3" -o output.mp3
```

**Full Editing (More Aggressive):**
```bash
python cleanvoice_enhancer.py "https://example.com/audio.mp3" -o output.mp3 \
  --fillers --mouth-sounds --long-silences --stutters
```

**Simple Denoising (Minimal Changes):**
```bash
python cleanvoice_enhancer.py "https://example.com/audio.mp3" -o output.mp3 \
  --remove-noise --normalize
```

### All Enhancement Options

```
--remove-noise         Remove background noise (default: True)
--normalize            Normalize audio levels (default: True)
--fillers              Remove filler sounds (um, uh, like)
--mouth-sounds         Remove mouth sounds and clicks
--breath CHOICE        Breath control: natural|muted|legacy|false
--long-silences        Remove long silences
--stutters             Remove stutters
--studio-sound TYPE    Studio processing: false|nightly (default: nightly)
--keep-delete          Keep files on servers (auto-delete after 7 days)
```

### Command-Line Arguments

```
positional arguments:
  input                 Public URL(s) to audio/video file(s) (required)

optional arguments:
  -h, --help            Show help message and exit
  -o, --output OUTPUT   Output file or directory (required)
  --api-key API_KEY     CleanVoice API key (or set CLEANVOICE_API_KEY env)
  [enhancement options listed above]
```

## Python Module Usage

```python
from cleanvoice_enhancer import CleanVoiceEnhancer

# Initialize
enhancer = CleanVoiceEnhancer(api_key="your_api_key")

# Single file
enhancer.enhance_file(
    file_url="https://example.com/audio.mp3",
    output_path="output.mp3"
)

# With custom config
config = {
    "remove_noise": True,
    "normalize": True,
    "fillers": True,
    "mouth_sounds": True,
    "studio_sound": "nightly"
}

enhancer.enhance_file(
    file_url="https://example.com/audio.mp3",
    output_path="output.mp3",
    config=config
)

# Multiple files
enhancer.enhance_batch(
    file_urls=[
        "https://example.com/file1.mp3",
        "https://example.com/file2.mp3"
    ],
    output_dir="enhanced"
)
```

## Supported Formats

### Input Formats
- Audio: MP3, WAV, AAC, M4A, FLAC, OGG
- Video: MP4, MOV, MKV (audio track extracted)

### Output Format
- MP3 (default, universal compatibility)

### Supported Languages
- Full Support: English, German, Romanian
- Partial Support: French, Dutch, Bulgarian, Arabic, Turkish, Polish, Italian, Spanish, Portuguese

## Processing Details

### What CleanVoice Does

**Noise Reduction:**
- Removes background noise (traffic, fans, AC, etc.)
- Reduces room echo and reverb
- Eliminates hum and buzzing
- Cleans up environmental artifacts
- Preserves music in background if enabled

**Filler Word Detection:**
- Identifies: um, uh, like, basically, you know, etc.
- Intelligently removes them
- Preserves natural speech flow
- Language-aware detection

**Silence & Breath Handling:**
- Detects and reduces long silences
- Breath control options:
  - "natural": Reduce volume, keep presence
  - "muted": Fully remove breaths
  - "legacy": Older algorithm (for already-good audio)

**Mouth Sound Removal:**
- Removes clicks, pops, smacking sounds
- Reduces lip noise
- Maintains clarity

**Studio Sound Processing:**
- "nightly": Recommended, newer algorithm with professional results
- Applies EQ and compression
- Makes audio sound professional

**Audio Normalization:**
- Consistent loudness levels
- Prevents clipping and distortion
- Professional broadcast standard

### Processing Speed

**Typical Times:**
- 5-minute audio: 2-5 minutes
- 30-minute podcast: 10-20 minutes
- 1-hour podcast: 30-60 minutes
- Usually faster than realtime

**Why Variable:**
- Server load
- File complexity
- Selected enhancements
- Audio quality

### Edit Statistics

After processing, you'll see statistics:
```
Edit Statistics:
  BREATH: 340
  DEADAIR: 124
  STUTTERING: 2
  MOUTH_SOUND: 5
  FILLER_SOUND: 17
```

This shows what was detected and edited.

## Examples

### Example 1: Enhance Podcast Episode

```bash
# 1. Upload to S3
aws s3 cp raw_podcast.mp3 s3://my-bucket/raw_podcast.mp3 --acl public-read

# 2. Get URL
URL="https://my-bucket.s3.amazonaws.com/raw_podcast.mp3"

# 3. Enhance
python cleanvoice_enhancer.py "$URL" -o clean_podcast.mp3
```

### Example 2: Full Editing for Interview

```bash
python cleanvoice_enhancer.py \
  "https://my-bucket.s3.amazonaws.com/interview.mp3" \
  -o interview_clean.mp3 \
  --fillers --mouth-sounds --long-silences --studio-sound nightly
```

### Example 3: Batch Process Podcast Series

```bash
# Upload all episodes to S3
for file in episodes/*.mp3; do
    aws s3 cp "$file" "s3://my-bucket/$file" --acl public-read
done

# Create URLs file
cat > urls.txt << EOF
https://my-bucket.s3.amazonaws.com/episodes/ep1.mp3
https://my-bucket.s3.amazonaws.com/episodes/ep2.mp3
https://my-bucket.s3.amazonaws.com/episodes/ep3.mp3
EOF

# Batch process
python cleanvoice_enhancer.py \
  $(cat urls.txt | tr '\n' ' ') \
  -o enhanced_episodes/
```

### Example 4: Video Enhancement Workflow

```bash
# 1. Extract audio from video
ffmpeg -i video.mp4 -vn -acodec libmp3lame audio.mp3

# 2. Upload to S3
aws s3 cp audio.mp3 s3://my-bucket/audio.mp3 --acl public-read

# 3. Enhance
python cleanvoice_enhancer.py \
  "https://my-bucket.s3.amazonaws.com/audio.mp3" \
  -o enhanced.mp3

# 4. Mix back with video
python mixer.py videos/video.mp4 enhanced.mp3 -o final.mp4
```

## Pricing

### CleanVoice Pricing
- **Pay-per-use model**
- Check official pricing at [https://cleanvoice.ai](https://cleanvoice.ai)
- Typically affordable for content creators
- Volume discounts may be available

### Cost Estimation
```
Example: 30-minute podcast
Check cleanvoice.ai for current rates

Typical range: $1-$5 depending on enhancements
```

## Troubleshooting

### Error: "API key required"
```bash
export CLEANVOICE_API_KEY="your_api_key_here"
echo $CLEANVOICE_API_KEY  # Verify it's set
```

### Error: "No download URL"
- Edit job failed or timed out
- Check CleanVoice dashboard for errors
- Try again with simpler configuration

### Error: "Public URL required"
- You passed a local file path instead of URL
- Upload file to S3 or cloud storage first
- Use public URL instead

### Processing Takes Too Long
- Normal for longer files
- Check CleanVoice dashboard status
- Very long files (>2 hours) may take longer
- Don't interrupt process

### Quality Issues
**Try different settings:**
```bash
# For very clean audio, use legacy breath algorithm
--breath legacy

# For noisy audio, add more processing
--fillers --mouth-sounds --long-silences

# For professional result
--studio-sound nightly
```

## File Cleanup

CleanVoice automatically deletes files after 7 days. To delete sooner:

```bash
# Script automatically deletes after download
# To keep files on servers, use:
--keep-delete
```

## Complete Workflow Example

```bash
#!/bin/bash

# 1. Convert to MP3 if needed
ffmpeg -i raw_audio.wav -c:a libmp3lame -q:a 2 audio.mp3

# 2. Upload to S3
aws s3 cp audio.mp3 s3://my-bucket/audio.mp3 --acl public-read
URL="https://my-bucket.s3.amazonaws.com/audio.mp3"

# 3. Enhance
python cleanvoice_enhancer.py "$URL" -o enhanced.mp3 \
    --fillers --mouth-sounds --studio-sound nightly

# 4. Use enhanced audio (e.g., mix with video)
python mixer.py video.mp4 enhanced.mp3 -o final.mp4
```

## Support & Resources

- **CleanVoice Website:** [https://cleanvoice.ai](https://cleanvoice.ai)
- **API Documentation:** [https://cleanvoice.ai/api](https://cleanvoice.ai/api)
- **API Playground:** [https://app.cleanvoice.ai/playground/](https://app.cleanvoice.ai/playground/)
- **Script Help:** `python cleanvoice_enhancer.py --help`
- **Support:** support@cleanvoice.ai
- 
## Version

Current Version: 2.0.0 (CleanVoice API v2)

## Author

Angel Molina

---

**Important:** Remember to upload files to public storage (S3, GCS, etc.) before processing!
