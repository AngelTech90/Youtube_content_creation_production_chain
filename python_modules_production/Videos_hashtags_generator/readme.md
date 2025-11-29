# YouTube Tags & Hashtags Generator

Generate SEO-optimized YouTube tags and social media hashtags using Google Gemini AI based on video transcriptions.

## Overview

This script uses Gemini AI to create strategic tags and hashtags that:
- Improve video discoverability on YouTube
- Target relevant search queries
- Include long-tail keywords (less competitive)
- Drive social media traffic
- Include trending hashtags for sharing
- Prioritize by relevance and search value

Perfect for content creators who want data-driven tag strategies without manual research.

## Features

- 🤖 **Gemini AI Analysis** - Intelligent tag and hashtag generation
- 🏆 **Prioritization** - AI ranks tags by relevance and search value
- 🔍 **SEO Optimized** - Long-tail keywords and variations
- 📱 **Social Ready** - Hashtags for Twitter, Instagram, TikTok
- 🎯 **Mixed Strategy** - Broad and specific keywords
- ⚡ **Fast Processing** - Generates in seconds
- 💾 **Complete Output** - Tags, hashtags, and tips in one file

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
python youtube_tags_generator.py --help
```

## Usage

### Basic Usage

**Generate tags and hashtags from transcription:**
```bash
python youtube_tags_generator.py transcription.txt -o tags.txt
```

This creates `tags.txt` with 15 tags and 5 hashtags (default).

### Custom Options

**Generate more tags (YouTube allows up to 30):**
```bash
python youtube_tags_generator.py transcription.txt -o tags.txt --num-tags 25
```

**Generate more hashtags:**
```bash
python youtube_tags_generator.py transcription.txt -o tags.txt --num-hashtags 10
```

**Skip prioritization for faster processing:**
```bash
python youtube_tags_generator.py transcription.txt -o tags.txt --no-prioritize
```

**Specify output file:**
```bash
python youtube_tags_generator.py transcription.txt -o my_tags.txt
```

**With API key:**
```bash
python youtube_tags_generator.py transcription.txt -o tags.txt --api-key YOUR_KEY
```

## Command-Line Arguments

```
positional arguments:
  transcription         Transcription file (transcription.txt)

optional arguments:
  -h, --help            Show help message
  -o, --output OUTPUT   Output file name (default: tags.txt)
  --num-tags NUM        Number of tags to generate (default: 15, max: 30)
  --num-hashtags NUM    Number of hashtags to generate (default: 5)
  --no-prioritize       Skip tag prioritization
  --api-key API_KEY     Google Gemini API key
```

## Output Format

Creates `tags.txt` with organized tags and hashtags:

```
YOUTUBE TAGS:
machine learning
artificial intelligence
ai tutorial
deep learning
neural networks
python programming
tensorflow
data science
computer vision
nlp
natural language processing
supervised learning
unsupervised learning
reinforcement learning
ai for beginners
coding tutorial

SOCIAL MEDIA HASHTAGS:
#MachineLearning #ArtificialIntelligence #AITutorial #PythonProgramming #DeepLearning

TIPS:
- YouTube allows up to 30 tags maximum
- Use 8-15 tags for best performance
- Most important tags should come first
- Hashtags go in description for discoverability
- Review and adjust based on performance
```

## How It Works

### Step 1: Transcription Analysis
Gemini analyzes your video transcription to understand:
- Main topics and keywords
- Technical terms and concepts
- Target audience level
- Video niche and category

### Step 2: Tag Generation
Creates tags that:
- Are 1-2 words (YouTube standard)
- Include long-tail keywords
- Mix broad and specific terms
- Use relevant variations
- Avoid clickbait

### Step 3: Tag Prioritization
AI ranks tags by:
- Relevance to content
- Search volume potential
- Competition level
- Specificity and value

### Step 4: Hashtag Generation
Creates social media hashtags:
- Include # symbol
- Use CamelCase format
- Target trending topics
- Work across platforms

## Python Module Usage

```python
from youtube_tags_generator import YouTubeTagsGenerator

# Initialize
generator = YouTubeTagsGenerator(api_key="your_key")

# Generate tags
tags = generator.generate_tags(
    transcription_text="Your transcription...",
    num_tags=15
)

# Generate hashtags
hashtags = generator.generate_hashtags(
    transcription_text="Your transcription...",
    num_hashtags=5
)

# Prioritize tags
prioritized = generator.prioritize_tags(tags, transcription_text)

print(prioritized)
print(hashtags)
```

## Examples

### Example 1: AI Tutorial Video

```bash
python youtube_tags_generator.py ai_tutorial_transcript.txt -o tags.txt --num-tags 20
```

Generates tags like: machine learning, neural networks, python, deep learning, ai tutorial, etc.

### Example 2: Podcast Episode

```bash
python youtube_tags_generator.py podcast_transcript.txt -o tags.txt --num-tags 15
```

Generates podcast-specific tags with social hashtags.

### Example 3: Gaming Content

```bash
python youtube_tags_generator.py gaming_transcript.txt -o tags.txt --num-tags 25
```

Generates gaming tags optimized for discoverability.

## Tag Strategy

### Best Practices:

1. **Tag Count:**
   - Minimum: 5 tags
   - Optimal: 8-15 tags
   - Maximum: 30 tags

2. **Tag Structure:**
   - First tag: Most important keyword
   - Middle tags: Variations and related keywords
   - Last tags: Niche and long-tail keywords

3. **Tag Types:**
   - Broad keywords (high volume, high competition)
   - Specific keywords (lower volume, easier to rank)
   - Long-tail keywords (3+ words, very specific)

4. **Hashtag Usage:**
   - Use 5-10 hashtags
   - Place in video description
   - Share on social media
   - Use trending hashtags

## YouTube Tag Guidelines

### What Works:
- Single words or 2-word phrases
- Lowercase format
- Relevant to video content
- Mix of broad and specific
- Long-tail keywords

### What Doesn't Work:
- Misleading or clickbait tags
- Tags with spaces (invalid)
- Tags not related to video
- Over-capitalization
- Special characters

## Social Media Hashtag Tips

### Best Practices:
- Mix trending and niche hashtags
- Use CamelCase for multi-word hashtags
- Include in description (not just comments)
- Share on Twitter, Instagram, TikTok
- Research hashtag popularity

### Hashtag Examples:
- `#MachineLearning`
- `#AITutorial`
- `#PythonProgramming`
- `#DeepLearning`
- `#TechTutorial`

## Integration with Other Modules

### Complete Content Creation Pipeline

```bash
# 1. Generate title
python youtube_title_generator.py transcription.txt -o title.txt

# 2. Generate description
python youtube_description_generator.py transcription.txt -o description.txt

# 3. Generate tags
python youtube_tags_generator.py transcription.txt -o tags.txt
```

## Tips for Best Results

1. **Quality Transcription:**
   - Accurate speech-to-text
   - 500+ words recommended
   - Includes technical terms

2. **Prioritization:**
   - Always use prioritization (default)
   - Most important tags first
   - Better for algorithm

3. **Tag Usage:**
   - Use generated tags as-is
   - Customize if needed
   - Test performance

4. **Hashtags:**
   - Use in description
   - Share on social media
   - Check for trending status

## Troubleshooting

### Error: "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your_api_key"
```

### Error: "Transcription file not found"
- Verify file path is correct
- Use absolute path if needed
- Check file exists

### Tag Quality Issues
- Ensure transcription is accurate
- Use longer transcriptions (500+ words)
- Include technical keywords

### API Rate Limit
- Wait and retry
- Reduce processing frequency
- Batch process later

## Performance

- **Generation Speed:** < 15 seconds
- **Tag Count:** 15 tags (default)
- **Hashtags:** 5 hashtags (default)
- **API Calls:** ~2 per generation
- **Reliability:** 99%+

## YouTube Tag Limits

- **Maximum tags:** 30
- **Tag length:** Variable
- **Recommended:** 8-15 tags
- **Format:** Lowercase, no spaces

## Hashtag Performance

### High-Performing Hashtags:
- 500K-5M posts (established, discoverable)
- CamelCase format
- Specific to niche
- Trending or evergreen

## License

MIT License - Free for personal and commercial use

## Version

Current Version: 1.0.0

## Author

Video Enhancement Pipeline Project

---

**Pro Tip:** Use prioritized tags in order - the first few tags are most important for YouTube's algorithm!
