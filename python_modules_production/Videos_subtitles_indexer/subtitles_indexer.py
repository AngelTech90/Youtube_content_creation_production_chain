#!/usr/bin/env python3
"""
AI-Powered Subtitle Generator & Injector
Analyze transcriptions with Gemini AI, generate optimal subtitles,
and inject them into videos with custom fonts via FFmpeg
"""

import subprocess
import sys
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import google.generativeai as genai
from dotenv import load_dotenv


def get_first_file(directory: str, extension: str) -> Optional[str]:
    """Get first file with given extension in directory"""
    try:
        path = Path(directory)
        for file in path.glob(f"*{extension}"):
            return str(file)
    except Exception:
        pass
    return None


class GeminiTranscriptionAnalyzer:
    """Analyze transcriptions using Google Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini analyzer
        
        Args:
            api_key: Google Gemini API key (or set GEMINI_API_KEY environment variable)
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google Gemini API key required.\n"
                "Set GEMINI_API_KEY environment variable or pass api_key parameter.\n"
                "Get your API key at: https://ai.google.dev/\n"
                "Free tier available with generous limits"
            )
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def analyze_transcription(self, transcription_text: str) -> List[Dict]:
        """
        Analyze transcription with Gemini AI to extract optimal subtitle segments
        
        Uses AI to:
        - Identify sentence boundaries
        - Find natural pause points
        - Suggest optimal subtitle timing
        - Group related content
        
        Args:
            transcription_text: Full transcription text or path to file
            
        Returns:
            List of dictionaries with 'text' and 'timestamps' for each subtitle
        """
        # Load from file if path provided
        if isinstance(transcription_text, str) and transcription_text.endswith(('.txt', '.srt', '.vtt')):
            with open(transcription_text, 'r', encoding='utf-8') as f:
                transcription_text = f.read()
        
        print("Analyzing transcription with Gemini AI...")
        
        prompt = f"""Analyze this transcription and create *very sparse, high-impact subtitle highlights*.

Purpose:
- These are not regular subtitles — they are **visual emphasis cues**.
- Each subtitle should contain only 1–3 key words that visually reinforce the spoken content.
- Subtitles should appear **rarely** (roughly 1 every 15–30 seconds of speech).
- Never place two subtitles close together — always ensure clear spacing between them.
- Choose only the most meaningful, emotionally strong, or visually significant words or short phrases.
- Avoid filler words, full sentences, or literal transcription.
- Focus on variety and rhythm — the subtitles should feel like accent marks in the video.

For each chosen moment, output:
1. `"text"` – the short highlight (1–3 impactful words)
2. `"duration"` – 1.0–2.0 seconds (short flashes)
3. `"importance"` – `"high"` only for core emotional/semantic peaks

Return ONLY valid JSON array like:
[
  {{
    "text": "keyword highlight",
    "duration": 1.5,
    "importance": "high"
  }},
  ...
]

TRANSCRIPTION:
{transcription_text}

Return only the JSON array:"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON in Gemini response")
            
            json_str = json_match.group(0)
            segments = json.loads(json_str)

            # Enforce very sparse distribution — at least 10 seconds between subtitles
            min_gap = 10.0
            filtered = []
            last_end = -min_gap
            for seg in segments:
                start = seg.get("start", 0.0)
                if start - last_end >= min_gap:
                    filtered.append(seg)
                    last_end = seg.get("end", start + seg.get("duration", 1.5))
            segments = filtered
            print(f"✓ Enforced sparse spacing: {len(segments)} total subtitles")
            

            # Reduce subtitles to roughly 1/4 of original amount
            if len(segments) > 4:
                reduced_count = max(1, len(segments) // 4)
                step = len(segments) / reduced_count
                segments = [segments[int(i * step)] for i in range(reduced_count)]
                print(f"⚙ Reduced to {len(segments)} subtitles (1/4 frequency)")

            
            print(f"✓ Analyzed {len(segments)} subtitle segments")
            return segments
            
        except Exception as e:
            raise Exception(f"Gemini analysis failed: {str(e)}")
    
    def enhance_subtitles(self, segments: List[Dict]) -> List[Dict]:
        """
        Use Gemini AI to enhance subtitle quality
        
        - Improve phrasing
        - Check grammar
        - Ensure readability
        - Optimize timing
        """
        if not segments:
            return segments
        
        print("Enhancing subtitles with Gemini AI...")
        
        # Format segments for Gemini
        formatted_segments = "\n".join([
            f"{i+1}. ({s.get('duration', 3)}s) {s.get('text', '')}"
            for i, s in enumerate(segments)
        ])
        
        prompt = f"""Review these video subtitles and provide improvements:

Current subtitles:
{formatted_segments}

Improve them by:
1. Ensuring they're readable (40-60 chars per line)
2. Checking grammar and spelling
3. Making timing appropriate for readability
4. Keeping natural speech patterns

Return ONLY valid JSON array with improved segments:
[
  {{
    "text": "Improved text",
    "duration": 3.5,
    "importance": "high|medium|low"
  }},
  ...
]

Return only the JSON array:"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                enhanced = json.loads(json_str)
                print(f"✓ Enhanced {len(enhanced)} subtitle segments")
                return enhanced
            
            return segments
            
        except Exception as e:
            print(f"⚠ Enhancement skipped: {str(e)}")
            return segments
    
    def generate_timing(self, segments: List[Dict]) -> List[Dict]:
        """
        Use Gemini to generate precise timing based on content
        Considers:
        - Word count for reading time
        - Importance level
        - Natural pauses
        """
        print("Generating optimal timing with Gemini AI...")

        formatted_segments = "\n".join([
            f"{i+1}. ({s.get('importance', 'medium')}) {s.get('text', '')}"
            for i, s in enumerate(segments)
        ])

        prompt = f"""For these subtitle texts, calculate optimal timing:

Segments:
{formatted_segments}

Calculate duration for each based on:
- Reading speed (150–180 words per minute)
- Importance level (high=5-6s, medium=3-4s, low=2-3s)
- Natural speech pacing

Return ONLY JSON with start/end times in seconds:
[
  {{
    "text": "Text",
    "start": 0.0,
    "end": 3.5,
    "duration": 3.5,
    "importance": "high|medium|low"
  }},
  ...
]

Assume first subtitle starts at 0s.
Return only the JSON array:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON in Gemini timing response")

            json_str = json_match.group(0)
            timed = json.loads(json_str)
            print(f"✓ Generated timing for {len(timed)} segments")

            # 🔽 Enforce sparse, highlight-only subtitle distribution
            min_gap = 15.0  # seconds between subtitles
            filtered = []
            last_end = -min_gap
            for seg in timed:
                start = seg.get("start", 0.0)
                if start - last_end >= min_gap:
                    filtered.append(seg)
                    last_end = seg.get("end", start + seg.get("duration", 1.5))

            # 🔽 Limit total subtitle count (change 10 as needed)
            filtered = filtered[:10]
            print(f"✓ Enforced sparse spacing: {len(filtered)} subtitles kept")

            return filtered

        except Exception as e:
            raise Exception(f"Gemini timing generation failed: {str(e)}")

class SubtitleGenerator:
    """Generate SRT subtitle files"""
    
    @staticmethod
    def generate_srt(segments: List[Dict], output_path: str):
        """
        Generate SRT subtitle file from segments
        
        Args:
            segments: List of segments with start, end, text, duration
            output_path: Path to save SRT file
        """
        # Calculate cumulative timing if not provided
        current_time = 0.0
        for segment in segments:
            if 'start' not in segment:
                segment['start'] = current_time
            if 'end' not in segment:
                duration = segment.get('duration', 3.0)
                segment['end'] = segment['start'] + duration
            current_time = segment['end']
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start_time = SubtitleGenerator._seconds_to_srt_time(seg['start'])
                end_time = SubtitleGenerator._seconds_to_srt_time(seg['end'])
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{seg['text']}\n")
                f.write("\n")
        
        print(f"✓ SRT file generated: {output_path}")
    
    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')


class SubtitleInjector:
    """Inject subtitles into videos using FFmpeg"""
    
    def __init__(self, font_path: Optional[str] = None):
        """
        Initialize subtitle injector
        
        Args:
            font_path: Path to custom font file (.ttf)
        """
        self.font_path = font_path
        self.check_ffmpeg()
    
    def check_ffmpeg(self):
        """Verify FFmpeg is installed"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "FFmpeg not found. Install it:\n"
                "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  Fedora: sudo dnf install ffmpeg\n"
                "  macOS: brew install ffmpeg"
            )
    
    def inject_subtitles(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_size: int = 14,
        font_color: str = "white",
        border_width: int = 2,
        border_color: str = "none",
        background: bool = True,
        background_color: str = "black",
        background_alpha: float = 0.8
    ):
        """
        Inject subtitles into video using FFmpeg
        
        Args:
            video_path: Input video file
            srt_path: SRT subtitle file
            output_path: Output video file
            font_size: Font size in pixels
            font_color: Subtitle text color
            border_width: Border width around text
            border_color: Border color
            background: Add background box
            background_color: Background box color
            background_alpha: Background transparency (0.0-1.0)
        """
        video_path = Path(video_path)
        srt_path = Path(srt_path)
        output_path = Path(output_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        if not srt_path.exists():
            raise FileNotFoundError(f"SRT file not found: {srt_path}")
        
        print(f"\nInjecting subtitles into: {video_path.name}")
        print(f"Subtitle file: {srt_path.name}")
        print(f"Font: {self.font_path if self.font_path else 'System default'}")
        
        # Build subtitle filter
        subtitle_filter = self._build_subtitle_filter(
            srt_path,
            font_size,
            font_color,
            border_width,
            border_color,
            background,
            background_color,
            background_alpha
        )
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '18',
            '-c:a', 'aac',
            '-b:a', '320k',
            '-y',
            str(output_path)
        ]
        
        print("Running FFmpeg...")
        try:
            subprocess.run(cmd, check=True)
            print(f"✓ Subtitled video saved: {output_path}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg error: {str(e)}")
    
    def _build_subtitle_filter(
        self,
        srt_path: Path,
        font_size: int,
        font_color: str,
        border_width: 0,
        border_color: str,
        background: bool,
        background_color: str,
            background_alpha: float
    ) -> str:
            
            """
            Build a robust FFmpeg subtitle filter that:
            - Converts SRT to ASS automatically (for better styling)
            - Applies font size, color, border, and optional background box
            - Handles both .srt and .ass input files gracefully
            """

            srt_path = Path(srt_path)
            srt_path_str = str(srt_path).replace("\\", "/")

            # If input is .srt → convert to .ass for styling
            if srt_path.suffix.lower() == ".srt":
                ass_path = srt_path.with_suffix(".ass")

                print(f"Converting SRT → ASS for styling: {ass_path.name}")
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", srt_path_str, str(ass_path)],
                        check=True,
                        capture_output=True
                    )
                    srt_path_str = str(ass_path).replace("\\", "/")
                except subprocess.CalledProcessError as e:
                    print(f"⚠ SRT→ASS conversion failed, using plain SRT: {e}")

            # Build ASS-style force_style attributes
            # FFmpeg ASS colors use BGR hex with &H prefix, not RGB
            def to_ass_color(color_name: str) -> str:
                """Convert simple color names or hex (#RRGGBB) to ASS BGR hex (&HBBGGRR&)"""
                css_colors = {
                    "white": "FFFFFF",
                    "black": "000000",
                    "yellow": "00FFFF",
                    "red": "0000FF",
                    "green": "00FF00",
                    "blue": "FF0000",
                    "cyan": "FFFF00",
                    "magenta": "FF00FF",
                    "gray": "808080",
                }
                color_name = color_name.lower().strip()
                if color_name.startswith("#") and len(color_name) == 7:
                    rgb = color_name[1:]
                    # Convert RGB → BGR
                    return f"&H{rgb[4:6]}{rgb[2:4]}{rgb[0:2]}&"
                return f"&H{css_colors.get(color_name, 'FFFFFF')}&"

            ass_font_color = to_ass_color(font_color)
            ass_border_color = to_ass_color(border_color)

            # Background transparency handling
            force_style_parts = [
                f"Fontsize={font_size}",
                f"PrimaryColour={ass_font_color}",
                f"Outline={border_width}",
                f"OutlineColour={ass_border_color}",
            ]

            if background:
                alpha = int((1 - background_alpha) * 255)
                bg_alpha = 255 - alpha  # ASS alpha is inverted
                bg_color = to_ass_color(background_color)
                # Append alpha to color definition
                force_style_parts.append(f"BackColour={bg_color[:-1]}{bg_alpha:02X}&")

            if self.font_path:
                font_path_str = str(self.font_path).replace("\\", "/")
                font_name = Path(font_path_str).stem
                force_style_parts.append(f"FontName={font_name}")

            # Combine into ASS style string
            force_style = ",".join(force_style_parts)
            subtitle_filter = f"subtitles='{srt_path_str}':force_style='{force_style}'"

            print(f"Using subtitle filter: {subtitle_filter}")
            return subtitle_filter

class AISubtitleWorkflow:
    """Complete AI-powered subtitle workflow"""
    
    # Default paths
    DEFAULT_TRANSCRIPTION_DIR = Path("../../in_production_content/transcriptions")
    DEFAULT_VIDEO_DIR = Path("../../Pre_production_content/videos")
    DEFAULT_OUTPUT_DIR = Path("../../in_production_content/videos")
    DEFAULT_FONT_DIR = Path("../../Pre_production_content/fonts")
    
    def __init__(self, api_key: Optional[str] = None, font_path: Optional[str] = None):
        # Create default directories
        self.DEFAULT_TRANSCRIPTION_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_FONT_DIR.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = GeminiTranscriptionAnalyzer(api_key=api_key)
        self.generator = SubtitleGenerator()
        self.injector = SubtitleInjector(font_path=font_path)
    
    def process(
        self,
        transcription_path: Optional[str] = None,
        video_path: Optional[str] = None,
        output_video_path: Optional[str] = None,
        srt_output_path: Optional[str] = None,
        enhance: bool = True,
        **kwargs
    ):
        """
        Complete AI workflow: analyze, enhance, generate timing, create SRT, inject
        
        Args:
            transcription_path: Path to transcription file (uses default if not specified)
            video_path: Path to input video (uses default if not specified)
            output_video_path: Path to output video with subtitles (uses default if not specified)
            srt_output_path: Optional path to save generated SRT file
            enhance: Use Gemini to enhance subtitle quality
            **kwargs: Additional arguments for subtitle injection
        """
        # Use defaults if not specified
        if not transcription_path:
            transcription_path = get_first_file(str(self.DEFAULT_TRANSCRIPTION_DIR), '.txt')
            if not transcription_path:
                raise FileNotFoundError(
                    f"No .txt files found in {self.DEFAULT_TRANSCRIPTION_DIR}"
                )
            print(f"Using transcription: {Path(transcription_path).name}")
        
        if not video_path:
            video_path = get_first_file(str(self.DEFAULT_VIDEO_DIR), '.mp4')
            if not video_path:
                raise FileNotFoundError(
                    f"No .mp4 files found in {self.DEFAULT_VIDEO_DIR}"
                )
            print(f"Using video: {Path(video_path).name}")
        
        if not output_video_path:
            output_video_path = self.DEFAULT_OUTPUT_DIR / "subtitled_video.mp4"
        else:
            output_video_path = Path(output_video_path)
            if not output_video_path.is_absolute():
                output_video_path = self.DEFAULT_OUTPUT_DIR / output_video_path
        
        if not srt_output_path:
            srt_output_path = self.DEFAULT_OUTPUT_DIR / "subtitles.srt"
        else:
            srt_output_path = Path(srt_output_path)
            if not srt_output_path.is_absolute():
                srt_output_path = self.DEFAULT_OUTPUT_DIR / srt_output_path
        
        print(f"\n{'='*60}")
        print("AI-POWERED SUBTITLE GENERATION WORKFLOW")
        print('='*60)
        
        # Step 1: Load transcription
        print(f"\n[1/5] Loading transcription: {transcription_path}")
        with open(transcription_path, 'r', encoding='utf-8') as f:
            transcription_text = f.read()
        print(f"✓ Loaded {len(transcription_text)} characters")
        
        # Step 2: Analyze with Gemini
        print(f"\n[2/5] Analyzing transcription with Gemini AI")
        segments = self.analyzer.analyze_transcription(transcription_text)
        print(f"✓ Generated {len(segments)} subtitle segments")
        
        # Step 3: Enhance (optional)
        if enhance:
            print(f"\n[3/5] Enhancing subtitles with Gemini AI")
            segments = self.analyzer.enhance_subtitles(segments)
        else:
            print(f"\n[3/5] Skipping enhancement (--no-enhance)")
        
        # Step 4: Generate timing
        print(f"\n[4/5] Generating optimal timing with Gemini AI")
        segments = self.analyzer.generate_timing(segments)
        
        # Generate SRT file
        print(f"\n Creating SRT file")
        self.generator.generate_srt(segments, str(srt_output_path))
        
        # Step 5: Inject into video
        print(f"\n[5/5] Injecting subtitles into video")
        self.injector.inject_subtitles(
            video_path,
            str(srt_output_path),
            str(output_video_path),
            **kwargs
        )
        
        print(f"\n{'='*60}")
        print("✓ WORKFLOW COMPLETE")
        print('='*60)
        print(f"Input video: {video_path}")
        print(f"Transcription: {transcription_path}")
        print(f"Output video: {output_video_path}")
        print(f"SRT subtitles: {srt_output_path}")
        print('='*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered subtitle generation and injection using Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default files from directories
  python subtitle_generator.py
  
  # Specify transcription file
  python subtitle_generator.py --transcription transcription.txt
  
  # Specify video file
  python subtitle_generator.py --video video.mp4
  
  # Custom output path
  python subtitle_generator.py -o output.mp4
  
  # With custom font
  python subtitle_generator.py --font Arial.ttf
  
  # Custom styling
  python subtitle_generator.py \\
      --font-size 32 \\
      --font-color yellow \\
      --border-width 3

Default Paths (modify in script):
  Transcriptions: ../../in_production_content/transcriptions
  Videos:         ../../in_production_content/enhanced_videos
  Output:         ../../Upload_stage/video_package
  Fonts:          ../../fonts

Environment:
  GEMINI_API_KEY    Your Google Gemini API key
        """
    )
    
    parser.add_argument(
        '--transcription', '-t',
        help='Transcription file (.txt) - uses default if not specified'
    )
    
    parser.add_argument(
        '--video', '-v',
        help='Input video file - uses default if not specified'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output video file with subtitles - uses default if not specified'
    )
    
    parser.add_argument(
        '--font',
        help='Path to custom font file (.ttf)'
    )
    
    parser.add_argument(
        '--srt-output',
        help='Path to save generated SRT file (optional)'
    )
    
    parser.add_argument(
        '--no-enhance',
        action='store_true',
        help='Skip Gemini enhancement (faster)'
    )
    
    parser.add_argument(
        '--api-key',
        help='Google Gemini API key'
    )
    
    # Styling options
    parser.add_argument(
        '--font-size',
        type=int,
        default=24,
        help='Font size in pixels (default: 24)'
    )
    
    parser.add_argument(
        '--font-color',
        default='white',
        help='Subtitle text color (default: white)'
    )
    
    parser.add_argument(
        '--border-width',
        type=int,
        default=2,
        help='Border width around text (default: 2)'
    )
    
    parser.add_argument(
        '--border-color',
        default='black',
        help='Border color (default: black)'
    )
    
    parser.add_argument(
        '--bg-color',
        default='black',
        help='Background box color (default: black)'
    )
    
    parser.add_argument(
        '--bg-alpha',
        type=float,
        default=0.8,
        help='Background transparency 0.0-1.0 (default: 0.8)'
    )
    
    parser.add_argument(
        '--no-background',
        action='store_true',
        help='Disable background box'
    )
    
    args = parser.parse_args()
    
    # Validate files if specified
    if args.transcription and not Path(args.transcription).exists():
        print(f"Error: Transcription file not found: {args.transcription}", file=sys.stderr)
        sys.exit(1)
    
    if args.video and not Path(args.video).exists():
        print(f"Error: Video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)
    
    if args.font and not Path(args.font).exists():
        print(f"Error: Font file not found: {args.font}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize workflow
    try:
        workflow = AISubtitleWorkflow(api_key=args.api_key, font_path=args.font)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process
    try:
        workflow.process(
            transcription_path=args.transcription,
            video_path=args.video,
            output_video_path=args.output,
            srt_output_path=args.srt_output,
            enhance=not args.no_enhance,
            font_size=args.font_size,
            font_color=args.font_color,
            border_width=args.border_width,
            border_color=args.border_color,
            background=not args.no_background,
            background_color=args.bg_color,
            background_alpha=args.bg_alpha
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
