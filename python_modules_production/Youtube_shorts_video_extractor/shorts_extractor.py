#!/usr/bin/env python3
"""
YouTube Shorts Generator
Analyze video transcription with Gemini AI to find optimal Shorts segments,
then automatically split video using FFmpeg
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


class ShortsTimestampAnalyzer:
    """Analyze transcription to find optimal YouTube Shorts timestamps"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize analyzer
        
        Args:
            api_key: Google Gemini API key
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
    
    def analyze_for_shorts(self, transcription_text: str, video_duration: float) -> List[Dict]:
        """
        Analyze transcription to find optimal YouTube Shorts segments
        
        YouTube Shorts are 15-60 seconds (optimal: 30-45 seconds)
        
        Args:
            transcription_text: Full video transcription
            video_duration: Total video duration in seconds
            
        Returns:
            List of segments with start, end, and content type
        """
        print("Analyzing transcription with Gemini AI for Shorts segments...")
        
        prompt = f"""You are a YouTube content expert. Analyze this video transcription and identify the best segments to create YouTube Shorts (15-60 seconds each, optimal: 30-45 seconds).

Requirements:
1. Find segments that are:
   - Self-contained and engaging
   - Have a clear hook or punchline
   - Don't cut off mid-sentence
   - Have strong visual/narrative potential
   - Work as standalone content

2. For each segment, identify:
   - The main topic/theme
   - Why it works as a Short
   - Engagement potential (high/medium/low)
   - Best use case (tutorial, entertainment, educational, motivational, funny, etc.)

3. Segment duration: 30-45 seconds is ideal (15-60 max)

Video Duration: {video_duration} seconds
Transcription: {transcription_text}

Analyze the transcription and identify 5-10 optimal Shorts segments.

Return ONLY valid JSON array with NO additional text:
[
  {{
    "title": "Short title/hook",
    "content_type": "tutorial|entertainment|educational|motivational|tip|funny|story",
    "theme": "Brief theme description",
    "engagement": "high|medium|low",
    "reason": "Why this works as a Short",
    "approximate_duration_seconds": 35,
    "segment_description": "What happens in this segment"
  }},
  ...
]

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
            
            print(f"✓ Identified {len(segments)} optimal Shorts segments")
            return segments
            
        except Exception as e:
            raise Exception(f"Gemini analysis failed: {str(e)}")
    
    def generate_timestamps(self, segments: List[Dict], transcription_text: str, video_duration: float) -> List[Dict]:
        """
        Use Gemini to generate precise timestamps for each segment
        
        Args:
            segments: Segments from analysis
            transcription_text: Full transcription
            video_duration: Total video duration
            
        Returns:
            Segments with exact start and end timestamps
        """
        print("Generating precise timestamps with Gemini AI...")
        
        segments_desc = "\n".join([
            f"{i+1}. {s['title']} - {s['segment_description']}"
            for i, s in enumerate(segments)
        ])
        
        prompt = f"""You are a video editor. Map these YouTube Shorts segment descriptions to exact timestamps in the video.

Video Duration: {video_duration} seconds

Segments to locate:
{segments_desc}

Transcription (with approximate timing):
{transcription_text[:2000]}...

For each segment, estimate:
1. Start timestamp (HH:MM:SS)
2. End timestamp (HH:MM:SS)
3. Duration in seconds
4. Confidence level (high/medium/low)

Ensure:
- Each segment is 30-45 seconds optimal (15-60 max)
- Segments don't overlap
- Natural pause points for cuts
- Clean audio boundaries

Return ONLY valid JSON:
[
  {{
    "title": "Segment title",
    "start": "00:00:05",
    "end": "00:00:40",
    "duration_seconds": 35,
    "confidence": "high|medium|low"
  }},
  ...
]

Return only the JSON array:"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON in Gemini response")
            
            json_str = json_match.group(0)
            timestamps = json.loads(json_str)
            
            print(f"✓ Generated timestamps for {len(timestamps)} segments")
            return timestamps
            
        except Exception as e:
            raise Exception(f"Timestamp generation failed: {str(e)}")


class VideoSplitter:
    """Split video into segments using FFmpeg"""
    
    def __init__(self):
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
    
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using FFmpeg"""
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'json',
                    video_path
                ],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except Exception as e:
            raise Exception(f"Failed to get video duration: {str(e)}")
    
    def split_video(self, video_path: str, timestamp: Dict, output_dir: str, short_index: int):
        """
        Split video segment using FFmpeg
        
        Args:
            video_path: Path to input video
            timestamp: Dict with start, end, title
            output_dir: Directory to save shorts
            short_index: Index for naming
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize title for filename
        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', timestamp['title'])
        output_file = output_dir / f"short_{short_index:02d}_{safe_title}.mp4"
        
        print(f"  [{short_index}] {timestamp['title']}")
        print(f"      {timestamp['start']} - {timestamp['end']}")
        
        try:
            subprocess.run([
                'ffmpeg',
                '-i', str(video_path),
                '-ss', timestamp['start'],
                '-to', timestamp['end'],
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                '-crf', '23',
                '-y',
                str(output_file)
            ], capture_output=True, check=True)
            
            print(f"      ✓ Saved: {output_file.name}")
            return str(output_file)
            
        except subprocess.CalledProcessError as e:
            print(f"      ✗ Failed to create short")
            return None
    
    def split_all_segments(self, video_path: str, timestamps: List[Dict], output_dir: str) -> List[str]:
        """Split all shorts segments"""
        output_files = []
        
        print(f"\nSplitting video into {len(timestamps)} Shorts:\n")
        
        for i, timestamp in enumerate(timestamps, 1):
            output_file = self.split_video(video_path, timestamp, output_dir, i)
            if output_file:
                output_files.append(output_file)
        
        return output_files


class ShortsWorkflow:
    """Complete YouTube Shorts generation workflow"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.analyzer = ShortsTimestampAnalyzer(api_key=api_key)
        self.splitter = VideoSplitter()
    
    def process(self, transcription_path: str, video_path: str, output_dir: str):
        """
        Complete workflow: analyze transcription, generate timestamps, split video
        
        Args:
            transcription_path: Path to transcription.txt
            video_path: Path to input video
            output_dir: Directory to save Shorts
        """
        print(f"\n{'='*60}")
        print("YOUTUBE SHORTS GENERATOR")
        print('='*60)
        
        # Step 1: Load transcription
        print(f"\n[1/5] Loading transcription: {transcription_path}")
        transcription_text = self.analyzer.load_transcription(transcription_path)
        print(f"✓ Loaded {len(transcription_text)} characters")
        
        # Step 2: Get video duration
        print(f"\n[2/5] Analyzing video: {video_path}")
        video_duration = self.splitter.get_video_duration(video_path)
        print(f"✓ Video duration: {video_duration:.1f} seconds ({int(video_duration)//60}:{int(video_duration)%60:02d})")
        
        # Step 3: Analyze for Shorts segments
        print(f"\n[3/5] Analyzing for Shorts segments")
        segments = self.analyzer.analyze_for_shorts(transcription_text, video_duration)
        
        # Step 4: Generate timestamps
        print(f"\n[4/5] Generating precise timestamps")
        timestamps = self.analyzer.generate_timestamps(segments, transcription_text, video_duration)
        
        # Step 5: Split video
        print(f"\n[5/5] Creating Shorts videos")
        output_files = self.splitter.split_all_segments(video_path, timestamps, output_dir)
        
        # Summary
        print(f"\n{'='*60}")
        print("✓ COMPLETE")
        print('='*60)
        print(f"Input video: {video_path}")
        print(f"Transcription: {transcription_path}")
        print(f"Shorts created: {len(output_files)}")
        print(f"Output directory: {output_dir}")
        print('='*60 + "\n")
        
        return output_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate YouTube Shorts from video using Gemini AI for timestamp analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Shorts from transcription and video
  python youtube_shorts_generator.py transcription.txt video.mp4 -o shorts/
  
  # With API key
  python youtube_shorts_generator.py transcription.txt video.mp4 -o shorts/ --api-key YOUR_KEY

Output:
  - Creates multiple MP4 files in output directory
  - Each file is a standalone YouTube Short (30-45 seconds optimal)
  - Files named: short_01_title.mp4, short_02_title.mp4, etc.

Environment:
  GEMINI_API_KEY    Your Google Gemini API key
        """
    )
    
    parser.add_argument(
        'transcription',
        help='Transcription file (transcription.txt)'
    )
    
    parser.add_argument(
        'video',
        help='Input video file'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='shorts',
        help='Output directory for Shorts (default: shorts/)'
    )
    
    parser.add_argument(
        '--api-key',
        help='Google Gemini API key'
    )
    
    args = parser.parse_args()
    
    # Validate files
    if not Path(args.transcription).exists():
        print(f"Error: Transcription file not found: {args.transcription}", file=sys.stderr)
        sys.exit(1)
    
    if not Path(args.video).exists():
        print(f"Error: Video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize workflow
    try:
        workflow = ShortsWorkflow(api_key=args.api_key)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process
    try:
        workflow.process(
            transcription_path=args.transcription,
            video_path=args.video,
            output_dir=args.output
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
