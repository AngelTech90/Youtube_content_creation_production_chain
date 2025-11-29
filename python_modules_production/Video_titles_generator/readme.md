# YouTube Title Generator

Generate engaging, SEO-optimized YouTube video titles using Google Gemini AI based on video transcriptions.

## Overview

This script uses Gemini AI to analyze your video transcription and generate multiple compelling YouTube titles that:
- Are SEO-optimized with relevant keywords
- Meet YouTube's character limits (50-60 characters)
- Include power words for engagement
- Have high click-through rate potential

Perfect for content creators who want AI-generated titles without manual brainstorming.

## Features

- 🤖 **Gemini AI Analysis** - Intelligent title generation from transcription
- 📊 **Multiple Titles** - Generate 5-10 title variations
- 🏆 **Best Selection** - AI selects the best title automatically
- 🔍 **SEO Optimized** - Keywords and engagement optimization
- ⚡ **Fast Processing** - Generates titles in seconds
- 💾 **Simple Output** - Single title.txt file with best option

## Requirements

### System Requirements
- Python 3.7 or higher
- Google Gemini API key

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

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set Gemini API key
export GEMINI_API_KEY="your_api_key_here"

# 4. Test
python youtube_title_generator.py --help
```

## Usage

### Basic Usage

**Generate title from transcription:**
```bash
python youtube_title_generator.py transcription.txt -o title.txt
```

This creates `title.txt` with the best YouTube title.

### Custom Options

**Generate more title variations:**
```bash
python youtube_title_generator.py transcription.txt -o title.txt --num-titles 10
```

**Specify output file:**
```bash
python youtube_title_generator.py transcription.txt -o my_title.txt
```

**With API key:**
```bash
python youtube_title_generator.py transcription.txt -o title.txt --api-key YOUR_KEY
```

## Command-Line Arguments

```
positional arguments:
  transcription         Transcription file (transcription.txt)

optional arguments:
  -h, --help            Show help message
  -o, --output OUTPUT   Output file name (default: title.txt)
  --num-titles NUM      Number of titles to generate (default: 5)
  --api-key API_KEY     Google Gemini API key
```

## Output Format

Creates `title.txt` with a single line containing the best generated title:

```
The Ultimate Guide to AI Video Production: Everything You Need to Know
```

## How It Works

### Step 1: Transcription Analysis
Gemini analyzes your video transcription to understand:
- Main topic and keywords
- Audience and niche
- Key points and hooks
- Content value

### Step 2: Title Generation
Generates multiple titles with:
- Relevant keywords for SEO
- Power words (Ultimate, Amazing, Best, etc.)
- Proper length (50-60 characters)
- Emotional/curiosity appeal

### Step 3: Selection
AI selects the best title based on:
- SEO potential
- Click-through rate likelihood
- Audience engagement
- Clarity and description

## Python Module Usage

```python
from youtube_title_generator import YouTubeTitleGenerator

# Initialize
generator = YouTubeTitleGenerator(api_key="your_key")

# Generate titles
titles = generator.generate_titles(
    transcription_text="Your transcription here...",
    num_titles=5
)

# Select best
best_title = generator.select_best_title(titles)
print(best_title)
```

## Examples

### Example 1: Simple Podcast Episode

```bash
python youtube_title_generator.py podcast_transcript.txt -o title.txt
```

### Example 2: Tutorial Video

```bash
python youtube_title_generator.py tutorial_script.txt -o title.txt --num-titles 10
```

### Example 3: Batch Processing

```bash
#!/bin/bash
for transcription in transcriptions/*.txt; do
    output="titles/$(basename $transcription .txt)_title.txt"
    python youtube_title_generator.py "$transcription" -o "$output"
done
```

## Title Characteristics

### Generated Titles Include:
- **Keywords:** Relevant to your video topic
- **Power Words:** Amazing, Incredible, Best, Ultimate, etc.
- **Length:** Optimal 50-60 characters
- **Clarity:** Descriptive and understandable
- **Appeal:** Emotional or curiosity-driven

### What Gemini Avoids:
- Misleading or clickbait titles
- Too many special characters
- Redundant keywords
- Vague descriptions

## Gemini Free Tier

### Rate Limits
- 60 requests per minute
- 15 requests per second
- Perfect for content creation
- No cost

### Usage Estimate
- 1 title generation: ~2 API calls
- Batch of 20 videos: ~40 calls
- Well within free tier

## Integration with Other Modules

### Complete Content Creation Pipeline

```bash
# 1. Generate title
python youtube_title_generator.py transcription.txt -o title.txt

# 2. Generate description
python youtube_description_generator.py transcription.txt -o description.txt

# 3. Generate tags/hashtags
python youtube_tags_generator.py transcription.txt -o tags.txt
```

## Tips for Best Results

1. **Good Transcription:**
   - Accurate speech-to-text
   - Clean formatting
   - Includes key points

2. **Context Matters:**
   - More detailed transcription = better titles
   - Include topic keywords naturally
   - Better flow helps AI understand content

3. **Multiple Variations:**
   - Use `--num-titles 10` to see more options
   - Gemini picks the best, but you can review

4. **Customization:**
   - Use generated title as base
   - Modify as needed for your style
   - Mix and match different titles

## Troubleshooting

### Error: "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your_api_key"
```

### Error: "Transcription file not found"
- Verify file path is correct
- Use absolute path if needed
- Check file exists

### Title Quality Issues
- Ensure transcription is accurate
- Transcription should be 300+ words
- Include key points and keywords naturally

### API Rate Limit
- Wait a moment and retry
- Reduce `--num-titles` value
- Batch process later

## Output Examples

### Example 1: Tech Tutorial
```
Master Python AI Integration: Complete 2024 Guide
```

### Example 2: Business Podcast
```
The Future of Remote Work: Expert Insights & Predictions
```

### Example 3: Educational Content
```
Understanding Machine Learning: Beginners to Advanced
```

## Best Practices

1. **Keywords:** Include 2-3 main keywords naturally
2. **Length:** Stay within 50-60 characters
3. **Grammar:** Always proper spelling and grammar
4. **Accuracy:** Title should match video content
5. **Testing:** A/B test different variations on YouTube

## Performance

- **Generation Speed:** < 10 seconds
- **Processing:** Real-time
- **API Calls:** ~2 per generation
- **Reliability:** 99%+

## License

MIT License - Free for personal and commercial use

## Version

Current Version: 1.0.0

## Author

Video Enhancement Pipeline Project

---

**Pro Tip:** Generate titles for your last 10 videos to see what works best for your channel!
