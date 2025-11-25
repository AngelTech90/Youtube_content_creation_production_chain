#!/usr/bin/env python3
"""
YouTube Description Generator
Generate engaging, SEO-optimized YouTube video descriptions using Gemini AI
"""

import sys
import os
from pathlib import Path
from typing import Optional
import argparse
import google.generativeai as genai


class YouTubeDescriptionGenerator:
    """Generate YouTube descriptions using Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize description generator
        
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
    
    def generate_description(self, transcription_text: str, max_length: int = 5000) -> str:
        """
        Generate YouTube video description using Gemini AI
        
        Args:
            transcription_text: Full video transcription
            max_length: Maximum description length (YouTube allows 5000 chars)
            
        Returns:
            Generated description
        """
        print("Generating YouTube description with Gemini AI...")
        
        prompt = f"""You are a YouTube content expert. Create a compelling, SEO-optimized YouTube video description based on this transcription.

Requirements:
- 300-1000 words (optimal for SEO and engagement)
- First 2-3 lines should be the hook (most important, shown before "show more")
- Include 3-5 relevant keywords naturally throughout
- Include a call-to-action (like, subscribe, comment)
- Add a "What You'll Learn" section if applicable
- Include timestamps if the video has chapters (use HH:MM:SS format)
- Professional yet friendly tone
- Break into paragraphs for readability
- End with social media links or channel promotion

Video Transcription:
{transcription_text}

Generate the description now. It should be compelling and optimized for YouTube's algorithm:"""
        
        try:
            response = self.model.generate_content(prompt)
            description = response.text.strip()
            
            # Ensure it doesn't exceed max length
            if len(description) > max_length:
                description = description[:max_length].rsplit(' ', 1)[0] + "..."
            
            print(f"✓ Generated description ({len(description)} characters)")
            return description
            
        except Exception as e:
            raise Exception(f"Gemini description generation failed: {str(e)}")
    
    def optimize_description(self, description: str, keywords: Optional[list] = None) -> str:
        """
        Use Gemini to optimize description for better SEO
        
        Args:
            description: Initial description
            keywords: Optional list of keywords to emphasize
            
        Returns:
            Optimized description
        """
        print("Optimizing description with Gemini AI...")
        
        keywords_str = ""
        if keywords:
            keywords_str = f"\nEmphasize these keywords: {', '.join(keywords)}"
        
        prompt = f"""Review and optimize this YouTube video description for better SEO and engagement:

Description:
{description}

{keywords_str}

Optimize by:
1. Strengthening the hook (first 2-3 lines)
2. Ensuring keywords appear naturally 3-5 times
3. Adding clear structure and paragraphs
4. Improving call-to-action
5. Keeping it engaging and readable

Return the optimized description, maintaining similar length and structure:"""
        
        try:
            response = self.model.generate_content(prompt)
            optimized = response.text.strip()
            print(f"✓ Optimized description")
            return optimized
            
        except Exception as e:
            print(f"⚠ Optimization skipped: {str(e)}")
            return description
    
    def process(self, transcription_path: str, output_path: str, keywords: Optional[list] = None, optimize: bool = True):
        """
        Complete workflow: load transcription, generate and optimize description
        
        Args:
            transcription_path: Path to transcription.txt
            output_path: Path to save description.txt
            keywords: Optional keywords to emphasize
            optimize: Whether to optimize the description
        """
        print(f"\n{'='*60}")
        print("YOUTUBE DESCRIPTION GENERATOR")
        print('='*60)
        
        # Step 1: Load transcription
        print(f"\n[1/3] Loading transcription: {transcription_path}")
        transcription_text = self.load_transcription(transcription_path)
        print(f"✓ Loaded {len(transcription_text)} characters")
        
        # Step 2: Generate description
        print(f"\n[2/3] Generating description")
        description = self.generate_description(transcription_text)
        
        # Step 3: Optimize (optional)
        if optimize:
            print(f"\n[3/3] Optimizing description")
            description = self.optimize_description(description, keywords)
        else:
            print(f"\n[3/3] Skipping optimization")
        
        # Save to file
        print(f"\nSaving description.txt: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(description)
        
        print(f"✓ Description saved ({len(description)} characters)\n")
        
        print('='*60)
        print("✓ COMPLETE")
        print('='*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SEO-optimized YouTube descriptions using Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate description from transcription
  python youtube_description_generator.py transcription.txt -o description.txt
  
  # Add keywords to emphasize
  python youtube_description_generator.py transcription.txt -o description.txt \\
      --keywords "AI" "machine learning" "tutorial"
  
  # Skip optimization for faster processing
  python youtube_description_generator.py transcription.txt -o description.txt --no-optimize
  
  # With API key
  python youtube_description_generator.py transcription.txt -o description.txt --api-key YOUR_KEY

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
        default='description.txt',
        help='Output file name (default: description.txt)'
    )
    
    parser.add_argument(
        '--keywords',
        nargs='+',
        help='Keywords to emphasize in description'
    )
    
    parser.add_argument(
        '--no-optimize',
        action='store_true',
        help='Skip optimization step'
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
        generator = YouTubeDescriptionGenerator(api_key=args.api_key)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process
    try:
        generator.process(
            transcription_path=args.transcription,
            output_path=args.output,
            keywords=args.keywords,
            optimize=not args.no_optimize
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
