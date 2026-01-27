#!/usr/bin/env python3
"""
YouTube Description Generator
Generate engaging, SEO-optimized YouTube video descriptions using Gemini AI
"""

import sys
import os
import re
from pathlib import Path
from typing import Optional, List
import argparse
import google.generativeai as genai
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip


# ============================================================
# Utility Functions
# ============================================================

def get_unprocessed_txt_files(path: str) -> List[str]:
    """Find all .txt files that don't have '_description' suffix"""
    txt_paths = []
    for root, _, files in os.walk(path, topdown=False):
        for name in files:
            if re.match(r'.*\.txt$', name) and '_description' not in name:
                txt_paths.append(os.path.join(root, name))
    return sorted(txt_paths)  # Sort for consistent processing order


def mark_file_as_processed(file_path: str) -> str:
    """Add '_description' suffix to filename"""
    path = Path(file_path)
    new_name = path.stem + "_description" + path.suffix
    new_path = path.parent / new_name
    path.rename(new_path)
    return str(new_path)


def get_mp4_path(path: str) -> Optional[str]:
    """Get first .mp4 file in directory"""
    try:
        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                if re.match(r'.*\.mp4$', name):
                    return os.path.join(root, name)
    except Exception as e:
        print(f"Error finding mp4 file: {e}")
    return None


def get_video_duration(video_path: Optional[str] = None) -> str:
    """Get video duration (seconds) for Gemini AI prompt"""
    if not video_path:
        video_path = get_mp4_path('../../Pre_production_content/videos')

    if not video_path:
        print("Warning: Could not find video file")
        return "60"

    try:
        if Path(video_path).exists():
            clip = VideoFileClip(video_path)
            duration_seconds = str(int(clip.duration))
            clip.close()
            return duration_seconds
        else:
            print(f"Warning: Video file not found: {video_path}")
            return "60"
    except Exception as e:
        print(f"Warning: Could not get video duration: {e}")
        return "60"

def get_first_available_package_dir(base_path: Path) -> Optional[Path]:
    """Get first directory in video_packages that doesn't have '_uploaded' suffix"""
    if not base_path.exists():
        return None

    subdirs = sorted([d for d in base_path.iterdir() if d.is_dir()])
    for subdir in subdirs:
        if '_uploaded' not in subdir.name:
            return subdir
    return None


# ============================================================
# Main Generator Class
# ============================================================

class YouTubeDescriptionGenerator:
    """Generate YouTube descriptions using Gemini AI"""

    DEFAULT_TRANSCRIPTION_DIR = Path("../../in_production_content/transcriptions/videos_transcriptions")
    DEFAULT_OUTPUT_DIR = Path("../../Upload_stage/videos_packages/")

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize description generator

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

    # -----------------------

    def load_transcription(self, transcription_path: str) -> str:
        """Load transcription from file"""
        with open(transcription_path, 'r', encoding='utf-8') as f:
            return f.read()

    # -----------------------

    def generate_description(self, transcription_text: str, max_length: int = 5000) -> str:
        """Generate YouTube video description using Gemini AI"""
        print("Generating YouTube description with Gemini AI...")

        
        contact_email = "juliajosefinaperez4@gmail.com"
        contact_whatsapp = "https://api.whatsapp.com/send/?phone=584143791814&text&type=phone_number&app_absent=0"

        prompt = f"""You are a YouTube content expert. Create a compelling, SEO-optimized YouTube video description based on this transcription.

Follow this templates depending of context in transcription:

Template A — Educational / Problem-Solving Video:

    If you're struggling with [core pain point], this video will give you the clarity you need.  
Today I’ll show you how to go from [Point A] to [Point B] using a simple, practical approach.

WHAT YOU’LL LEARN:
• Why [pain point] keeps happening  
• The steps to fix it without [common objection]  
• What to focus on first if you want real, lasting results  

WHO THIS IS FOR:
[Describe niche briefly]. If that’s you, you’re in the right place.

NEXT STEP:
If you want deeper guidance, download my free resource here: [link]

I help [your niche] achieve [specific transformation] using my [unique mechanism].  
Subscribe if you want a clear path toward [result].


Template B — Authority / Positioning Video:
    
    In this video, I break down the exact process I use to help my clients [achieve transformation].  
If you feel stuck in [pain point], this will help you understand what's missing and what truly works.

WHAT YOU'LL DISCOVER:
• The biggest misconceptions about [topic]  
• The proven method behind consistent results  
• How to avoid the mistakes that most people make  

ABOUT ME:
I help [your niche] go from [Point A] to [Point B] without [objection].  
My work is based on real client data, not theory.

NEXT STEP:
If you want help applying this to your life/business, you can join the waitlist or book a call here: [link]


Template C — Conversion-Focused Video:
    If you're ready to stop guessing and finally fix [pain point], this video will show you the exact path.  
This is the same process I use inside my [offer/program].

IN THIS VIDEO:
• The step-by-step roadmap to go from [A] to [B]  
• The unique method behind my clients’ results  
• What to do this week to start seeing progress  

READY FOR MORE?
If you're serious about [achieving result], apply here to work with me: [link]

I help [niche] solve [problem] with a clear, proven framework.  
Subscribe for weekly videos that get straight to the point.




Requirements:
- 300–1000 words (optimal for SEO and engagement)
- First 2–3 lines should be the hook (shown before "show more")
- Include 3–5 relevant keywords naturally
- Include a call-to-action (like, subscribe, comment)
- Add a "What You'll Learn" section if applicable
- Include timestamps if the video has chapters (use HH:MM:SS)
- Professional yet friendly tone
- Break into paragraphs for readability
- End with social media links or channel promotion

Video Transcription:
{transcription_text}

Social media links:
{contact_email}
{contact_whatsapp}

Generate the description now, optimized for YouTube's algorithm:
"""

        try:
            response = self.model.generate_content(prompt)
            description = response.text.strip()

            if len(description) > max_length:
                description = description[:max_length].rsplit(' ', 1)[0] + "..."

            print(f"✓ Generated description ({len(description)} characters)")
            return description

        except Exception as e:
            raise Exception(f"Gemini description generation failed: {str(e)}")

    # -----------------------

    def optimize_description(self, description: str, keywords: Optional[list] = None) -> str:
        """Use Gemini to optimize description for better SEO"""
        print("Optimizing description with Gemini AI...")

        keywords_str = ""
        if keywords:
            keywords_str = f"\nEmphasize these keywords: {', '.join(keywords)}"

        prompt = f"""Review and optimize this YouTube video description for better SEO and engagement:

Description:
{description}

{keywords_str}

Optimize by:
1. Strengthening the hook
2. Ensuring keywords appear naturally 3–5 times
3. Adding clear structure and paragraphs
4. Improving the call-to-action
5. Keeping it engaging and readable

Return the optimized description, maintaining similar length and tone:
"""

        try:
            response = self.model.generate_content(prompt)
            optimized = response.text.strip()
            print("✓ Optimized description")
            return optimized
        except Exception as e:
            print(f"⚠ Optimization skipped: {str(e)}")
            return description

    # -----------------------

    def process(
        self,
        transcription_path: Optional[str] = None,
        output_path: Optional[str] = None,
        keywords: Optional[list] = None,
        optimize: bool = True
    ):
        """Complete workflow: load transcription, generate, optimize, and save"""
        print(f"\n{'='*60}")
        print("YOUTUBE DESCRIPTION GENERATOR")
        print('='*60)

        # Step 1: Resolve transcription file
        if not transcription_path:
            txt_files = get_unprocessed_txt_files(str(self.DEFAULT_TRANSCRIPTION_DIR))
            if not txt_files:
                raise FileNotFoundError(
                    f"No unprocessed .txt files found in {self.DEFAULT_TRANSCRIPTION_DIR}"
                )
            transcription_path = txt_files[0]
            print(f"Using transcription: {Path(transcription_path).name}")

        # Step 2: Resolve output path
        if not output_path:
            package_dir = get_first_available_package_dir(self.DEFAULT_OUTPUT_DIR)
            if not package_dir:
                print("\n⚠ No available video package directories found (all may be uploaded)")
                print("Script execution ended.")
                sys.exit(0)

            output_path = package_dir / "description.txt"
            print(f"Output directory: {package_dir.name}")
        else:
            output_path = Path(output_path)
            if not output_path.is_absolute():
                output_path = self.DEFAULT_OUTPUT_DIR / output_path

        # Step 3: Load transcription
        print(f"\n[1/3] Loading transcription: {transcription_path}")
        transcription_text = self.load_transcription(transcription_path)
        print(f"✓ Loaded {len(transcription_text)} characters")

        # Step 4: Generate description
        print(f"\n[2/3] Generating description")
        description = self.generate_description(transcription_text)

        # Step 5: Optimize (optional)
        if optimize:
            print(f"\n[3/3] Optimizing description")
            description = self.optimize_description(description, keywords)
        else:
            print(f"\n[3/3] Skipping optimization")

        # Step 6: Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\nSaving description.txt: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(description)
        print(f"✓ Description saved ({len(description)} characters)\n")

        # Step 7: Mark transcription as processed
        print("Marking transcription as processed...")
        new_path = mark_file_as_processed(transcription_path)
        print(f"✓ Renamed to: {Path(new_path).name}\n")

        print('='*60)
        print("✓ COMPLETE")
        print('='*60 + "\n")


# ============================================================
# CLI Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate SEO-optimized YouTube descriptions using Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python descriptions_generator.py
  python descriptions_generator.py --transcription transcription.txt
  python descriptions_generator.py -o custom_description.txt
  python descriptions_generator.py --keywords "AI" "machine learning"
  python descriptions_generator.py --no-optimize
  python descriptions_generator.py --api-key YOUR_KEY
"""
    )

    parser.add_argument('--transcription', '-t', help='Transcription file path')
    parser.add_argument('-o', '--output', help='Output file name (default: description.txt)')
    parser.add_argument('--keywords', nargs='+', help='Keywords to emphasize')
    parser.add_argument('--no-optimize', action='store_true', help='Skip optimization step')
    parser.add_argument('--api-key', help='Google Gemini API key')

    args = parser.parse_args()

    if args.transcription and not Path(args.transcription).exists():
        print(f"Error: Transcription file not found: {args.transcription}", file=sys.stderr)
        sys.exit(1)

    try:
        generator = YouTubeDescriptionGenerator(api_key=args.api_key)
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

