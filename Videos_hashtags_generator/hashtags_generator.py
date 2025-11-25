#!/usr/bin/env python3
"""
YouTube Tags/Hashtags Generator
Generate SEO-optimized YouTube tags and hashtags using Gemini AI
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import argparse
import google.generativeai as genai


class YouTubeTagsGenerator:
    """Generate YouTube tags and hashtags using Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize tags generator
        
        Args:
            api_key: Google Gemini API key (or set GEMINI_API_KEY environment variable)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google Gemini API key required.\n"
                "Set GEMINI_API_KEY environment variable or pass api_key parameter.\n"
                "Get your API key at: https://ai.google.dev/"
            )
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def load_transcription(self, transcription_path: str) -> str:
        """Load transcription from file"""
        with open(transcription_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_tags(self, transcription_text: str, num_tags: int = 15) -> List[str]:
        """
        Generate YouTube tags using Gemini AI
        
        Args:
            transcription_text: Full video transcription
            num_tags: Number of tags to generate (YouTube allows max 30)
            
        Returns:
            List of generated tags
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
            
            # Ensure no duplicates
            tags = list(dict.fromkeys(tags))
            
            # Limit to requested number
            tags = tags[:num_tags]
            
            print(f"✓ Generated {len(tags)} YouTube tags")
            return tags
            
        except Exception as e:
            raise Exception(f"Gemini tag generation failed: {str(e)}")
    
    def generate_hashtags(self, transcription_text: str, num_hashtags: int = 5) -> List[str]:
        """
        Generate social media hashtags using Gemini AI
        
        Args:
            transcription_text: Full video transcription
            num_hashtags: Number of hashtags to generate
            
        Returns:
            List of generated hashtags
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
            
            # Ensure no duplicates
            hashtags = list(dict.fromkeys(hashtags))
            
            # Limit to requested number
            hashtags = hashtags[:num_hashtags]
            
            print(f"✓ Generated {num_hashtags} social media hashtags")
            return hashtags
            
        except Exception as e:
            raise Exception(f"Gemini hashtag generation failed: {str(e)}")
    
    def prioritize_tags(self, tags: List[str], transcription_text: str) -> List[str]:
        """
        Use Gemini to prioritize tags by relevance and search volume
        
        Args:
            tags: List of tags to prioritize
            transcription_text: Video transcription for context
            
        Returns:
            Prioritized list of tags
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
            
            # Filter to only tags that were in original list
            original_tags = set(t.lower() for t in tags)
            prioritized = [t for t in prioritized if t in original_tags]
            
            # Add any missing tags at the end
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
        
        # Tags section
        output += "YOUTUBE TAGS:\n"
        output += "\n".join(tags)
        output += "\n\n"
        
        # Hashtags section
        output += "SOCIAL MEDIA HASHTAGS:\n"
        output += " ".join(hashtags)
        output += "\n\n"
        
        # Tips section
        output += "TIPS:\n"
        output += "- YouTube allows up to 30 tags maximum\n"
        output += "- Use 8-15 tags for best performance\n"
        output += "- Most important tags should come first\n"
        output += "- Hashtags go in description for discoverability\n"
        output += "- Review and adjust based on performance\n"
        
        return output
    
    def process(self, transcription_path: str, output_path: str, num_tags: int = 15, num_hashtags: int = 5, prioritize: bool = True):
        """
        Complete workflow: generate tags and hashtags
        
        Args:
            transcription_path: Path to transcription.txt
            output_path: Path to save tags.txt
            num_tags: Number of tags to generate
            num_hashtags: Number of hashtags to generate
            prioritize: Whether to prioritize tags
        """
        print(f"\n{'='*60}")
        print("YOUTUBE TAGS & HASHTAGS GENERATOR")
        print('='*60)
        
        # Step 1: Load transcription
        print(f"\n[1/4] Loading transcription: {transcription_path}")
        transcription_text = self.load_transcription(transcription_path)
        print(f"✓ Loaded {len(transcription_text)} characters")
        
        # Step 2: Generate tags
        print(f"\n[2/4] Generating YouTube tags")
        tags = self.generate_tags(transcription_text, num_tags)
        
        # Step 3: Prioritize tags (optional)
        if prioritize:
            print(f"\n[3/4] Prioritizing tags")
            tags = self.prioritize_tags(tags, transcription_text)
        else:
            print(f"\n[3/4] Skipping tag prioritization")
        
        # Step 4: Generate hashtags
        print(f"\n[4/4] Generating social media hashtags")
        hashtags = self.generate_hashtags(transcription_text, num_hashtags)
        
        # Format and save
        output_content = self.format_output(tags, hashtags)
        
        print(f"\nSaving tags.txt: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        print(f"✓ Tags and hashtags saved\n")
        
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
  # Generate tags and hashtags
  python youtube_tags_generator.py transcription.txt -o tags.txt
  
  # Generate more tags
  python youtube_tags_generator.py transcription.txt -o tags.txt --num-tags 25
  
  # Skip prioritization for speed
  python youtube_tags_generator.py transcription.txt -o tags.txt --no-prioritize
  
  # With API key
  python youtube_tags_generator.py transcription.txt -o tags.txt --api-key YOUR_KEY

Environment:
  GEMINI_API_KEY    Your Google Gemini API key
        """
    )
    
    parser.add_argument(
        'transcription',
        help='Transcription file (transcription.txt)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='tags.txt',
        help='Output file name (default: tags.txt)'
    )
    
    parser.add_argument(
        '--num-tags',
        type=int,
        default=15,
        help='Number of tags to generate (default: 15, max: 30)'
    )
    
    parser.add_argument(
        '--num-hashtags',
        type=int,
        default=5,
        help='Number of hashtags to generate (default: 5)'
    )
    
    parser.add_argument(
        '--no-prioritize',
        action='store_true',
        help='Skip tag prioritization'
    )
    
    parser.add_argument(
        '--api-key',
        help='Google Gemini API key'
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not Path(args.transcription).exists():
        print(f"Error: Transcription file not found: {args.transcription}", file=sys.stderr)
        sys.exit(1)
    
    # Validate tag count
    if args.num_tags > 30:
        print("Warning: YouTube allows maximum 30 tags. Setting to 30.", file=sys.stderr)
        args.num_tags = 30
    
    # Initialize generator
    try:
        generator = YouTubeTagsGenerator(api_key=args.api_key)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process
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
