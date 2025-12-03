#!/usr/bin/env python3
"""
YouTube Tags/Hashtags Generator
Generate SEO-optimized YouTube tags and hashtags using Gemini AI
"""

import sys
import os
import re
from pathlib import Path
from typing import Optional, List
import argparse
import google.generativeai as genai
from dotenv import load_dotenv


def get_unused_txt_files(path: str) -> List[str]:
    """Find all .txt files that don't have '_used' suffix"""
    txt_paths = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if re.match(r'.*\.txt$', name) and '_hashtags' not in name:
                txt_paths.append(os.path.join(root, name))
    return sorted(txt_paths)  # Sort for consistent processing order


def mark_file_as_used(file_path: str) -> str:
    """Add '_used' suffix to filename"""
    path = Path(file_path)
    new_name = path.stem + "_hashtag" + path.suffix
    new_path = path.parent / new_name
    path.rename(new_path)
    return str(new_path)


def get_first_available_package_dir(base_path: Path) -> Optional[Path]:
    """Get first directory in video_packages that doesn't have '_uploaded' suffix"""
    if not base_path.exists():
        return None

    subdirs = sorted([d for d in base_path.iterdir() if d.is_dir()])
    for subdir in subdirs:
        if '_uploaded' not in subdir.name:
            return subdir
    return None

class YouTubeTagsGenerator:
    """Generate YouTube tags and hashtags using Gemini AI"""
    
    # Default base directory for transcriptions
    DEFAULT_TRANSCRIPTION_DIR = Path("../../in_production_content/transcriptions/videos_transcriptions")
    DEFAULT_OUTPUT_DIR = Path("../../Upload_stage/videos_packages/")
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize tags generator
        
        Args:
            api_key: Google Gemini API key (or set GEMINI_API_KEY environment variable)
        """
        self.DEFAULT_TRANSCRIPTION_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        load_dotenv()

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google Gemini API key required.\n"
                "Set GEMINI_API_KEY environment variable or pass api_key parameter.\n"
                "Get your API key at: https://ai.google.dev/"
            )
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def load_transcription(self, transcription_path: str) -> str:
        """Load transcription from file"""
        with open(transcription_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_tags(self, transcription_text: str, num_tags: int = 15) -> List[str]:
        """
        Generate YouTube tags using Gemini AI
        """
        print(f"Generating YouTube tags with Gemini AI...")
        
        prompt = f"""You are a YouTube SEO expert. Analyze this video transcription and generate {num_tags} highly relevant YouTube tags.

Requirements for tags:
- 1-2 words per tag (most effective on YouTube)
- Include long-tail keywords (less competitive)
- Mix broad and specific keywords
- Include variations and synonyms
- Use lowercase (YouTube standard)
- No special characters or spaces
- Avoid clickbait or misleading tags
- Target actual search queries people use

Tag Format:
- One tag per line
- No hashtags (#)
- No special characters
- 1-2 words max

Video Transcription:
{transcription_text}

Generate exactly {num_tags} high-quality YouTube tags. One per line, no numbering, no explanation:"""
        
        try:
            response = self.model.generate_content(prompt)
            tags = [t.strip().lower() for t in response.text.strip().split('\n') if t.strip()]
            
            tags = list(dict.fromkeys(tags))  # Remove duplicates
            tags = tags[:num_tags]  # Limit to requested number
            
            print(f"✓ Generated {len(tags)} YouTube tags")
            return tags
            
        except Exception as e:
            raise Exception(f"Gemini tag generation failed: {str(e)}")
    
    def generate_hashtags(self, transcription_text: str, num_hashtags: int = 5) -> List[str]:
        """
        Generate social media hashtags using Gemini AI
        """
        print(f"Generating social media hashtags with Gemini AI...")
        
        prompt = f"""You are a social media expert. Analyze this video transcription and generate {num_hashtags} trending, relevant hashtags for social sharing.

Requirements for hashtags:
- Include # symbol
- CamelCase for multi-word hashtags (example: #MachineLearning)
- Focus on trending topics
- Mix popular and niche hashtags
- Should work on Twitter, Instagram, TikTok
- 1-3 words per hashtag
- Relevant to video content

Hashtag Format:
- Include # symbol
- CamelCase format
- One per line
- No explanation

Video Transcription:
{transcription_text}

Generate exactly {num_hashtags} trending hashtags. One per line, with # symbol, no numbering:"""
        
        try:
            response = self.model.generate_content(prompt)
            hashtags = [h.strip() for h in response.text.strip().split('\n') if h.strip()]
            
            hashtags = list(dict.fromkeys(hashtags))  # Remove duplicates
            hashtags = hashtags[:num_hashtags]  # Limit
            
            print(f"✓ Generated {num_hashtags} social media hashtags")
            return hashtags
            
        except Exception as e:
            raise Exception(f"Gemini hashtag generation failed: {str(e)}")
    
    def prioritize_tags(self, tags: List[str], transcription_text: str) -> List[str]:
        """
        Use Gemini to prioritize tags by relevance and search volume
        """
        if len(tags) <= 1:
            return tags
        
        print("Prioritizing tags by relevance...")
        tags_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tags)])
        
        prompt = f"""You are a YouTube SEO expert. Rank these tags by importance and search value for this video.

Ranking criteria:
- Relevance to video content
- Search volume (higher is better)
- Competition level (lower is better for small channels)
- Specificity (long-tail keywords rank better)

Video Transcription (first 500 chars):
{transcription_text[:500]}...

Tags to rank:
{tags_str}

Return the tags in priority order, highest to lowest, one per line, no numbering, no explanation:"""
        
        try:
            response = self.model.generate_content(prompt)
            prioritized = [t.strip().lower() for t in response.text.strip().split('\n') if t.strip()]
            
            original_tags = set(t.lower() for t in tags)
            prioritized = [t for t in prioritized if t in original_tags]
            
            for tag in tags:
                if tag.lower() not in prioritized:
                    prioritized.append(tag.lower())
            
            print(f"✓ Tags prioritized")
            return prioritized
            
        except Exception as e:
            print(f"⚠ Prioritization skipped: {str(e)}")
            return tags
    
    def format_output(self, tags: List[str], hashtags: List[str]) -> str:
        """Format tags and hashtags for output file"""
        output = ""
        output += "YOUTUBE TAGS:\n" + "\n".join(tags) + "\n\n"
        output += "SOCIAL MEDIA HASHTAGS:\n" + " ".join(hashtags) + "\n\n"
        output += "TIPS:\n"
        output += "- YouTube allows up to 30 tags maximum\n"
        output += "- Use 8-15 tags for best performance\n"
        output += "- Most important tags should come first\n"
        output += "- Hashtags go in description for discoverability\n"
        output += "- Review and adjust based on performance\n"
        return output
    
    def process(self, transcription_path: Optional[str] = None, output_path: Optional[str] = None,
                num_tags: int = 15, num_hashtags: int = 5, prioritize: bool = True):
        """
        Complete workflow: generate tags and hashtags
        """
        print(f"\n{'='*60}")
        print("YOUTUBE TAGS & HASHTAGS GENERATOR")
        print('='*60)
        

        # Use default transcription if not specified
        if not transcription_path:
            txt_files = get_unused_txt_files(str(self.DEFAULT_TRANSCRIPTION_DIR))
            if not txt_files:
                raise FileNotFoundError(
                    f"No unused .txt files found in {self.DEFAULT_TRANSCRIPTION_DIR}"
                )
            transcription_path = txt_files[0]
            print(f"Using transcription: {Path(transcription_path).name}")
        

        # Use default output if not specified
        if not output_path:
            package_dir = get_first_available_package_dir(self.DEFAULT_OUTPUT_DIR)
            if not package_dir:
                print("\n⚠ No available video package directories found (all may be uploaded)")
                print("Script execution ended.")
                sys.exit(0)

            output_path = package_dir / "hashtags.txt"
            print(f"Output directory: {package_dir.name}")
        else:
            output_path = Path(output_path)
            if not output_path.is_absolute():
                output_path = self.DEFAULT_OUTPUT_DIR / output_path

        print(f"\n[1/4] Loading transcription: {transcription_path}")
        transcription_text = self.load_transcription(transcription_path)
        print(f"✓ Loaded {len(transcription_text)} characters")
        
        print(f"\n[2/4] Generating YouTube tags")
        tags = self.generate_tags(transcription_text, num_tags)
        
        if prioritize:
            print(f"\n[3/4] Prioritizing tags")
            tags = self.prioritize_tags(tags, transcription_text)
        else:
            print(f"\n[3/4] Skipping tag prioritization")
        
        print(f"\n[4/4] Generating social media hashtags")
        hashtags = self.generate_hashtags(transcription_text, num_hashtags)
        
        output_content = self.format_output(tags, hashtags)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nSaving tags.txt: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        print(f"✓ Tags and hashtags saved\n")
        
        print("Marking transcription as used...")
        new_path = mark_file_as_used(transcription_path)
        print(f"✓ Renamed to: {Path(new_path).name}\n")
        
        print('='*60)
        print("✓ COMPLETE")
        print('='*60)
        print(f"Tags generated: {len(tags)}")
        print(f"Hashtags generated: {len(hashtags)}")
        print('='*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SEO-optimized YouTube tags and hashtags using Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python youtube_tags_generator.py
  python youtube_tags_generator.py --transcription transcription.txt
  python youtube_tags_generator.py --num-tags 25
  python youtube_tags_generator.py --no-prioritize
  python youtube_tags_generator.py --api-key YOUR_KEY
"""
    )
    
    parser.add_argument('--transcription', '-t', help='Path to transcription file')
    parser.add_argument('-o', '--output', help='Output file name (default: tags.txt)')
    parser.add_argument('--num-tags', type=int, default=15, help='Number of tags (default 15, max 30)')
    parser.add_argument('--num-hashtags', type=int, default=5, help='Number of hashtags (default 5)')
    parser.add_argument('--no-prioritize', action='store_true', help='Skip tag prioritization')
    parser.add_argument('--api-key', help='Google Gemini API key')
    
    args = parser.parse_args()
    
    if args.num_tags > 30:
        print("Warning: YouTube allows maximum 30 tags. Setting to 30.", file=sys.stderr)
        args.num_tags = 30
    
    try:
        generator = YouTubeTagsGenerator(api_key=args.api_key)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        generator.process(
            transcription_path=args.transcription,
            output_path=args.output,
            num_tags=args.num_tags,
            num_hashtags=args.num_hashtags,
            prioritize=not args.no_prioritize
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

