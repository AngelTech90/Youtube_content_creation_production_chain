#!/usr/bin/env python3
"""
YouTube Shorts Generator (Default Paths Version)
Analyze video transcription with Gemini AI to find optimal Shorts segments,
then automatically split video using FFmpeg.
"""

import subprocess
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
import google.generativeai as genai


# ==============================
# DEFAULT CONFIGURATION
# ==============================
DEFAULT_TRANSCRIPTION = "../../in_production_content/transcriptions/*.txt"
DEFAULT_VIDEO = "../../Post_production_content/mixed_videos/*.mp4"
DEFAULT_OUTPUT = "../../Post_production_content/shorts"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Replace with your key or env var


class ShortsTimestampAnalyzer:
    """Analyze transcription to find optimal YouTube Shorts timestamps"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError(
                "Missing Gemini API key.\n"
                "Edit the script and set GEMINI_API_KEY or environment variable."
            )
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    def load_transcription(self, transcription_path: str) -> str:
        with open(transcription_path, "r", encoding="utf-8") as f:
            return f.read()

    def analyze_for_shorts(self, transcription_text: str, video_duration: float) -> List[Dict]:
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
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON in Gemini response")
            return json.loads(json_match.group(0))
        except Exception as e:
            raise Exception(f"Gemini analysis failed: {str(e)}")

    def generate_timestamps(self, segments: List[Dict], transcription_text: str, video_duration: float) -> List[Dict]:
        print("Generating precise timestamps with Gemini AI...")

        prompt = f"""You are a video editor...
        (prompt omitted for brevity — same as original)
        """
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON in Gemini response")
            return json.loads(json_match.group(0))
        except Exception as e:
            raise Exception(f"Timestamp generation failed: {str(e)}")


class VideoSplitter:
    """Split video into segments using FFmpeg"""

    def __init__(self):
        self.check_ffmpeg()

    def check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("FFmpeg not found. Please install FFmpeg to use this script.")

    def get_video_duration(self, video_path: str) -> float:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception as e:
            raise Exception(f"Failed to get video duration: {str(e)}")

    def split_video(self, video_path: str, timestamp: Dict, output_dir: str, short_index: int):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r"[^a-zA-Z0-9_-]", "_", timestamp["title"])
        output_file = output_dir / f"short_{short_index:02d}_{safe_title}.mp4"

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(video_path),
                    "-ss",
                    timestamp["start"],
                    "-to",
                    timestamp["end"],
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-y",
                    str(output_file),
                ],
                capture_output=True,
                check=True,
            )
            print(f"✓ Saved: {output_file.name}")
            return str(output_file)
        except subprocess.CalledProcessError:
            print(f"✗ Failed: {timestamp['title']}")
            return None

    def split_all_segments(self, video_path: str, timestamps: List[Dict], output_dir: str) -> List[str]:
        print(f"\nSplitting {len(timestamps)} segments...")
        return [f for i, t in enumerate(timestamps, 1)
                if (f := self.split_video(video_path, t, output_dir, i))]


class ShortsWorkflow:
    """End-to-end workflow"""

    def __init__(self, api_key: Optional[str] = None):
        self.analyzer = ShortsTimestampAnalyzer(api_key)
        self.splitter = VideoSplitter()

    def process(self, transcription_path: str, video_path: str, output_dir: str):
        print(f"\n{'='*60}\nYOUTUBE SHORTS GENERATOR\n{'='*60}")
        transcription_text = self.analyzer.load_transcription(transcription_path)
        print(f"✓ Loaded transcription ({len(transcription_text)} chars)")
        duration = self.splitter.get_video_duration(video_path)
        print(f"✓ Video duration: {duration:.1f}s")
        segments = self.analyzer.analyze_for_shorts(transcription_text, duration)
        timestamps = self.analyzer.generate_timestamps(segments, transcription_text, duration)
        self.splitter.split_all_segments(video_path, timestamps, output_dir)
        print(f"\nAll done! Shorts saved to: {output_dir}")


def main():
    # Ensure folders exist
    Path("data").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

    transcription = Path(DEFAULT_TRANSCRIPTION)
    video = Path(DEFAULT_VIDEO)
    output = Path(DEFAULT_OUTPUT)

    if not transcription.exists():
        raise FileNotFoundError(f"Missing transcription file: {transcription}")
    if not video.exists():
        raise FileNotFoundError(f"Missing video file: {video}")

    workflow = ShortsWorkflow(GEMINI_API_KEY)
    workflow.process(str(transcription), str(video), str(output))


if __name__ == "__main__":
    main()
