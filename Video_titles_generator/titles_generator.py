#!/usr/bin/env python3
"""
YouTube Title Generator
Generate engaging, SEO-optimized YouTube video titles using Gemini AI
"""

import sys
import os
from pathlib import Path
from typing import Optional
import argparse
import google.generativeai as genai


class YouTubeTitleGenerator:
    """Generate YouTube titles using Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize title generator
        
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
    
    def generate_titles(self, transcription_text: str, num_titles: int = 5) -> list:
        """
        Generate multiple YouTube video titles using Gemini AI
        
        Args:
            transcription_text: Full video transcription
            num_titles: Number of titles to generate
            
        Returns:
            List of generated titles
        """
        print("Generating YouTube titles with Gemini AI...")
        
        prompt = f"""You are a YouTube content strategist expert. Analyze this video transcription and generate {num_titles} engaging, clickable YouTube video titles.

Requirements for each title:
- Between 50-60 characters (optimal for YouTube)
- Include relevant keywords for SEO
- Create curiosity or emotional appeal
- Use power words (Amazing, Incredible, Best, Ultimate, etc.)
- Be clear and descriptive
- Avoid clickbait but be engaging
- No special characters or emojis

Video Transcription:
{transcription_text}

Generate EXACTLY {num_titles} titles, one per line. No numbering, no explanations, just the titles."""
        
        try:
            response = self.model.generate_content(prompt)
            titles = [t.strip() for t in response.text.strip().split('\n') if t.strip()]
            
            print(f"✓ Generated {len(titles)} YouTube titles")
            return titles
            
        except Exception as e:
            raise Exception(f"Gemini title generation failed: {str(e)}")
    
    def select_best_title(self, titles: list) -> str:
        """
        Use Gemini to select the best title from the generated list
        
        Args:
            titles: List of generated titles
            
        Returns:
            Best title selected by AI
        """
        if not titles:
            return ""
        
        if len(titles) == 1:
            return titles[0]
        
        print("Selecting best title with Gemini AI...")
        
        titles_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
        
        prompt = f"""You are a YouTube expert. Review these video titles and select the BEST one based on:
- SEO potential
- Click-through rate likelihood
- Audience engagement
- Clarity and description

Titles:
{titles_str}

Respond with ONLY the number (1-{len(titles)}) of the best title. No explanation, just the number."""
        
        try:
            response = self.model.generate_content(prompt)
            choice = response.text.strip()
            
            # Extract number from response
            import re
            match = re.search(r'\d+', choice)
            if match:
                index = int(match.group()) - 1
                if 0 <= index < len(titles):
                    best_title = titles[index]
                    print(f"✓ Selected best title: {best_title}")
                    return best_title
            
            return titles[0]
            
        except Exception as e:
            print(f"⚠ Failed to select best title: {str(e)}")
            return titles[0]
    
    def process(self, transcription_path: str, output_path: str, num_titles: int = 5):
        """
        Complete workflow: load transcription, generate titles, save to file
        
        Args:
            transcription_path: Path to transcription.txt
            output_path: Path to save title.txt
            num_titles: Number of titles to generate
        """
        print(f"\n{'='*60}")
        print("YOUTUBE TITLE GENERATOR")
        print('='*60)
        
        # Step 1: Load transcription
        print(f"\n[1/3] Loading transcription: {transcription_path}")
        transcription_text = self.load_transcription(transcription_path)
        print(f"✓ Loaded {len(transcription_text)} characters")
        
        # Step 2: Generate titles
        print(f"\n[2/3] Generating titles")
        titles = self.generate_titles(transcription_text, num_titles)
        
        # Step 3: Select best title
        print(f"\n[3/3] Selecting best title")
        best_title = self.select_best_title(titles)
        
        # Save to file
        print(f"\nSaving title.txt: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(best_title)
        
        print(f"✓ Title saved: {best_title}\n")
        
        print('='*60)
        print("✓ COMPLETE")
        print('='*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SEO-optimized YouTube titles using Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate title from transcription
  python youtube_title_generator.py transcription.txt -o title.txt
  
  # Generate multiple titles before selecting best
  python youtube_title_generator.py transcription.txt -o title.txt --num-titles 10
  
  # With API key
  python youtube_title_generator.py transcription.txt -o title.txt --api-key YOUR_KEY

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
        default='title.txt',
        help='Output file name (default: title.txt)'
    )
    
    parser.add_argument(
        '--num-titles',
        type=int,
        default=5,
        help='Number of titles to generate (default: 5)'
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
    
    # Initialize generator
    try:
        generator = YouTubeTitleGenerator(api_key=args.api_key)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process
    try:
        generator.process(
            transcription_path=args.transcription,
            output_path=args.output,
            num_titles=args.num_titles
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
