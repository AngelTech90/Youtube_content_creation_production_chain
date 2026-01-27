#!/usr/bin/env python3
"""
YouTube Title Generator
Generate engaging, SEO-optimized YouTube video titles using Gemini AI
"""

import sys
import os
import re
from pathlib import Path
from typing import Optional, List
import argparse
import google.generativeai as genai
from dotenv import load_dotenv


# -------------------------------------------------------
# Utility functions
# -------------------------------------------------------

def get_unprocessed_txt_files(path: str) -> List[str]:
    """Find all .txt files that don't have '_title' suffix"""
    txt_paths = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if re.match(r'.*\.txt$', name) and '_title' not in name:
                txt_paths.append(os.path.join(root, name))
    return sorted(txt_paths)  # Sort for consistent processing order


def mark_file_as_processed(file_path: str) -> str:
    """Add '_title' suffix to filename"""
    path = Path(file_path)
    new_name = path.stem + "_title" + path.suffix
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


# -------------------------------------------------------
# Main class
# -------------------------------------------------------

class YouTubeTitleGenerator:
    """Generate YouTube titles using Gemini AI"""

    # Default base directory for transcriptions
    DEFAULT_TRANSCRIPTION_DIR = Path("../../in_production_content/transcriptions/videos_transcriptions")
    DEFAULT_OUTPUT_DIR = Path("../../Upload_stage/videos_packages/")

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize title generator

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

    def generate_titles(self, transcription_text: str, num_titles: int = 5) -> list:
        """Generate multiple YouTube video titles using Gemini AI"""
        print("Generating YouTube titles with Gemini AI...")

        prompt = f"""You are a YouTube content strategist expert. Analyze this video transcription and generate {num_titles} engaging, clickable YouTube video titles.

Follow this template:


1. TITLE TEMPLATES (High-Performance YouTube Titles)
A. Problem–Solution Titles

How to [Achieve Result] Without [Pain/Obstacle]

The Simple Way to [Desired Outcome] (No Experience Needed)

What I’d Do Today to [Fix Core Problem] Fast

B. Error-Based Titles

Stop Making These [#] Mistakes That Ruin Your [Goal]

The Real Reason You're Not [Achieving Result] Yet

[#] Things Keeping You Stuck in [Pain Point]

C. Transformation / Promise Titles

From [Point A] to [Point B]: The Framework That Works

How I Help My Clients [Transformation] in [Timeframe]

The System I Used to [Big Result] With a Small Audience

D. Curiosity / Pattern-Interrupt Titles

You Don’t Need to Be Viral to [Achieve Result]

Everyone Does This Wrong When Trying to [Goal]

Nobody Talks About This Part of [Topic] — But It Changes Everything

Requirements for each title:
- Between 50-55 characters (optimal for YouTube)
- Include relevant keywords for SEO
- Create curiosity or emotional appeal
- Use power words (Amazing, Incredible, Best, Ultimate, etc.)
- Be clear and descriptive
- Avoid clickbait but be engaging
- No special characters or emojis
- Never add ":" in title 
- never use emojis
- Use upper word beig strategic
- Don'r repeat what thumbnail uses

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
        """Use Gemini to select the best title from the generated list"""
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

    def process(self, transcription_path: Optional[str] = None, output_path: Optional[str] = None, num_titles: int = 5):
        """Complete workflow: load transcription, generate titles, save to file"""
        print(f"\n{'='*60}")
        print("YOUTUBE TITLE GENERATOR")
        print('='*60)

        # Use default transcription if not specified
        if not transcription_path:
            txt_files = get_unprocessed_txt_files(str(self.DEFAULT_TRANSCRIPTION_DIR))
            if not txt_files:
                raise FileNotFoundError(
                    f"No unprocessed .txt files found in {self.DEFAULT_TRANSCRIPTION_DIR}"
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

            output_path = package_dir / "title.txt"
            print(f"Output directory: {package_dir.name}")
        else:
            output_path = Path(output_path)
            if not output_path.is_absolute():
                output_path = self.DEFAULT_OUTPUT_DIR / output_path

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
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\nSaving title.txt: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(best_title)

        print(f"✓ Title saved: {best_title}\n")

        # Mark transcription as processed
        print("Marking transcription as processed...")
        new_path = mark_file_as_processed(transcription_path)
        print(f"✓ Renamed to: {Path(new_path).name}\n")

        print('='*60)
        print("✓ COMPLETE")
        print('='*60 + "\n")


# -------------------------------------------------------
# Entry point
# -------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate SEO-optimized YouTube titles using Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python youtube_title_generator.py
  python youtube_title_generator.py --transcription transcription.txt
  python youtube_title_generator.py -o custom_title.txt
  python youtube_title_generator.py --num-titles 10
  python youtube_title_generator.py --api-key YOUR_KEY
"""
    )

    parser.add_argument('--transcription', '-t', help='Transcription file path')
    parser.add_argument('-o', '--output', help='Output file name')
    parser.add_argument('--num-titles', type=int, default=5, help='Number of titles to generate (default: 5)')
    parser.add_argument('--api-key', help='Google Gemini API key')

    args = parser.parse_args()

    if args.transcription and not Path(args.transcription).exists():
        print(f"Error: Transcription file not found: {args.transcription}", file=sys.stderr)
        sys.exit(1)

    try:
        generator = YouTubeTitleGenerator(api_key=args.api_key)
        generator.process(args.transcription, args.output, args.num_titles)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

