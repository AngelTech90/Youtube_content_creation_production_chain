#!/usr/bin/env python3
"""
YouTube Shorts Generator with Transcription Saving
--------------------------------------------------
Extracts optimal Shorts segments AND saves their transcription segments
for metadata generation.
"""
import subprocess
import os
import re
import json
from glob import glob
from pathlib import Path
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import argparse

# Default Configuration
DEFAULT_TRANSCRIPTION = Path("../../in_production_content/transcriptions/videos_transcriptions")
DEFAULT_VIDEO = Path("../../Upload_stage/videos_packages")
DEFAULT_OUTPUT = Path("../../Upload_stage/shorts_packages")
DEFAULT_SHORTS_TRANSCRIPTIONS = Path("../../in_production_content/transcriptions/shorts_transcriptions")

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def get_unprocessed_txt_files(path: Path) -> List[str]:
    """Find all .txt files that don't have '_hashtags', '_title', or '_description' suffix"""
    txt_paths = []
    for root, dirs, files in os.walk(str(path), topdown=False):
        for name in files:
            if (re.match(r'.*\.txt$', name)):
                txt_paths.append(os.path.join(root, name))
    return sorted(txt_paths)  # Sort for consistent processing order


def get_first_available_package_dir(base_path: Path) -> Optional[Path]:
    """Get first directory in packages that doesn't have '_uploaded' suffix"""
    if not base_path.exists():
        return None
    
    subdirs = sorted([d for d in base_path.iterdir() if d.is_dir()])
    
    for subdir in subdirs:
        if '_uploaded' not in subdir.name:
            return subdir
    
    return None


def mark_file_as_used(file_path: str) -> str:
    """Add '_shorts' suffix to filename"""
    path = Path(file_path)
    new_name = path.stem + "_shorts" + path.suffix
    new_path = path.parent / new_name
    path.rename(new_path)
    return str(new_path)


class ShortsTimestampAnalyzer:
    """Analyze transcription to find optimal YouTube Shorts timestamps"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Missing Gemini API key.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    def load_transcription(self, transcription_path: str) -> str:
        with open(transcription_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def analyze_for_shorts(self, transcription_text: str, video_duration: float) -> List[Dict]:
        print("Analyzing transcription with Gemini AI for Shorts segments...")
        
        prompt = f"""Analyze this video transcription and identify the best segments for YouTube Shorts (30-60 seconds each).

Requirements:
1. Self-contained, engaging segments
2. Clear hook or punchline
3. Not cut off mid-sentence
4. Strong visual/narrative potential
5. Work as standalone content

For each segment include:
- title: Catchy title
- content_type: tutorial | entertainment | educational | motivational | tip | story
- theme: Brief description
- engagement: high | medium | low
- reason: Why this works as a short
- approximate_duration_seconds: 30-60
- segment_description: What happens
- transcription_snippet: The EXACT text from transcription for this segment (IMPORTANT!)

Video Duration: {video_duration} seconds

Transcription:
{transcription_text}

Return ONLY valid JSON array:
[
  {{
    "title": "Short title",
    "content_type": "tutorial",
    "theme": "Main theme",
    "engagement": "high",
    "reason": "Why it works",
    "approximate_duration_seconds": 45,
    "segment_description": "What happens",
    "transcription_snippet": "Exact words spoken in this segment"
  }}
]
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON found")
            return json.loads(json_match.group(0))
        except Exception as e:
            raise Exception(f"Gemini analysis failed: {str(e)}")
    
    def generate_timestamps(self, segments: List[Dict], transcription_text: str, video_duration: float) -> List[Dict]:
        print("Generating precise timestamps with Gemini AI...")
        
        prompt = f"""Given these segments and full transcription, assign realistic timestamps (start and end in seconds) within a {video_duration}-second video.

RULES:
- Each segment lasts the approximate duration indicated
- Spread segments naturally across timeline
- Avoid overlap
- Ensure segments don't cut mid-sentence

Segments:
{json.dumps(segments, indent=2)}

Full Transcription:
{transcription_text}

Return only valid JSON array:
[
  {{
    "title": "Short title",
    "start": 15.0,
    "end": 55.0,
    "transcription_snippet": "Exact words from this time range"
  }}
]
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON found")
            
            timestamped = json.loads(json_match.group(0))
            
            # Merge with original segment data
            for i, ts in enumerate(timestamped):
                if i < len(segments):
                    ts.update({
                        'content_type': segments[i].get('content_type', 'entertainment'),
                        'theme': segments[i].get('theme', ''),
                        'segment_description': segments[i].get('segment_description', ''),
                        'transcription_snippet': ts.get('transcription_snippet', segments[i].get('transcription_snippet', ''))
                    })
            
            return timestamped
        except Exception as e:
            raise Exception(f"Timestamp generation failed: {str(e)}")


class VideoSplitter:
    """Split video into segments and save transcriptions"""
    
    def __init__(self):
        self.check_ffmpeg()
    
    def check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("FFmpeg not found.")
    
    def get_video_duration(self, video_path: str) -> float:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception as e:
            raise Exception(f"Failed to get video duration: {str(e)}")
    
    def save_transcription_snippet(self, snippet: str, output_dir: str, short_index: int, title: str):
        """Save transcription snippet for this short"""
        transcription_dir = Path(output_dir) / "transcriptions"
        transcription_dir.mkdir(parents=True, exist_ok=True)
        
        safe_title = re.sub(r"[^a-zA-Z0-9_-]", "_", title)
        transcription_file = transcription_dir / f"short_{short_index:02d}_{safe_title}.txt"
        
        try:
            with open(transcription_file, 'w', encoding='utf-8') as f:
                f.write(snippet)
            print(f"  ✓ Saved transcription: {transcription_file.name}")
            return str(transcription_file)
        except Exception as e:
            print(f"  ✗ Failed to save transcription: {e}")
            return None
    
    def split_video(self, video_path: str, timestamp: Dict, output_dir: str, short_index: int):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_title = re.sub(r"[^a-zA-Z0-9_-]", "_", timestamp["title"])
        output_file = output_dir / f"short_{short_index:02d}_{safe_title}.mp4"
        
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", str(video_path),
                    "-ss", str(timestamp["start"]),
                    "-to", str(timestamp["end"]),
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-preset", "fast",
                    "-crf", "23",
                    "-y", str(output_file),
                ],
                capture_output=True,
                check=True,
            )
            print(f"✓ Saved video: {output_file.name}")
            
            # Save transcription snippet
            snippet = timestamp.get('transcription_snippet', '')
            if snippet:
                self.save_transcription_snippet(snippet, str(output_dir), short_index, timestamp['title'])
            
            return str(output_file)
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to split video: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate YouTube Shorts from video with AI-powered segment analysis"
    )
    
    parser.add_argument(
        "--transcription", "-t",
        help="Path to transcription file (default: first unprocessed in default directory)"
    )
    
    parser.add_argument(
        "--video", "-v",
        help="Path to video file (default: first available in videos_packages)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output directory for shorts (default: shorts_packages)"
    )
    
    parser.add_argument(
        "--api-key",
        help="Google Gemini API key"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("YOUTUBE SHORTS EXTRACTOR WITH TRANSCRIPTIONS")
    print("="*60 + "\n")
    
    # Get transcription file
    if args.transcription:
        transcription = args.transcription
    else:
        txt_files = get_unprocessed_txt_files(DEFAULT_TRANSCRIPTION)
        if not txt_files:
            print("✗ No unprocessed transcription files found")
            return
        transcription = txt_files[0]
    
    print(f"📄 Using transcription: {Path(transcription).name}")
    
    # Get video file
    if args.video:
        video = args.video
    else:
        video_package_dir = get_first_available_package_dir(DEFAULT_VIDEO)
        if not video_package_dir:
            print("✗ No available video package directories found")
            return
        
        # Find first MP4 in the package directory
        video_files = list(video_package_dir.glob("*.mp4"))
        if not video_files:
            print(f"✗ No MP4 files found in {video_package_dir}")
            return
        
        video = str(video_files[0])
    
    print(f"🎥 Using video: {Path(video).name}")
    
    # Get output directory
    if args.output:
        output = args.output
    else:
        output = DEFAULT_OUTPUT
    
    # Create shorts package directory
    package_name = f"shorts_package_{Path(video).stem}"
    output_dir = Path(output) / package_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    print()
    
    try:
        # Initialize components
        analyzer = ShortsTimestampAnalyzer(api_key=args.api_key)
        splitter = VideoSplitter()
        
        # Step 1: Load transcription
        print("[1/5] Loading transcription...")
        transcription_text = analyzer.load_transcription(transcription)
        print(f"✓ Loaded {len(transcription_text)} characters\n")
        
        # Step 2: Get video duration
        print("[2/5] Analyzing video...")
        video_duration = splitter.get_video_duration(video)
        print(f"✓ Video duration: {video_duration:.1f} seconds\n")
        
        # Step 3: Analyze for shorts segments
        print("[3/5] Finding optimal shorts segments...")
        segments = analyzer.analyze_for_shorts(transcription_text, video_duration)
        print(f"✓ Found {len(segments)} potential segments\n")
        
        # Step 4: Generate timestamps
        print("[4/5] Generating precise timestamps...")
        timestamped_segments = analyzer.generate_timestamps(segments, transcription_text, video_duration)
        print(f"✓ Generated {len(timestamped_segments)} timestamped segments\n")
        
        # Step 5: Split video and save transcriptions
        print(f"[5/5] Creating {len(timestamped_segments)} shorts...")
        
        created_shorts = []
        for i, timestamp in enumerate(timestamped_segments, 1):
            print(f"\n  [{i}/{len(timestamped_segments)}] {timestamp['title']}")
            print(f"      Time: {timestamp['start']:.1f}s - {timestamp['end']:.1f}s")
            
            output_file = splitter.split_video(video, timestamp, str(output_dir), i)
            if output_file:
                created_shorts.append(output_file)
        
        print(f"\n✓ Successfully created {len(created_shorts)} shorts")
        print(f"✓ Saved to: {output_dir}")
        
        # Save segments metadata
        metadata_file = output_dir / "segments_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(timestamped_segments, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved metadata: {metadata_file.name}")
        
        # Mark transcription as processed
        print("\nMarking transcription as processed...")
        new_path = mark_file_as_used(transcription)
        print(f"✓ Renamed to: {Path(new_path).name}")
        
        print("\n" + "="*60)
        print("✓ COMPLETE")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
