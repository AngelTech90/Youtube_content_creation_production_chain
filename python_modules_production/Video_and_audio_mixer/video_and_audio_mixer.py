#!/usr/bin/env python3
"""
Video/Audio Mixer with Package Creation
Creates timestamped video packages ready for upload
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Dict
import argparse
import json
from datetime import datetime


class MediaMixer:
    """Mix video and audio streams and create upload packages"""

    DEFAULT_VIDEO_DIR = Path("../../in_production_content/enhanced_videos")
    DEFAULT_AUDIO_DIR = Path("../../in_production_content/enhanced_audios")
    DEFAULT_OUTPUT_DIR = Path("../../Upload_stage/videos_packages/")

    def __init__(self):
        """Initialize mixer and ensure directories exist"""
        for path in [self.DEFAULT_VIDEO_DIR, self.DEFAULT_AUDIO_DIR, self.DEFAULT_OUTPUT_DIR]:
            path.mkdir(parents=True, exist_ok=True)
        self.check_ffmpeg()

    def check_ffmpeg(self):
        """Ensure FFmpeg is available"""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")

    def get_duration(self, file_path: str) -> float:
        """Get duration in seconds using ffprobe"""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", file_path],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception:
            return 0.0

    def create_video_package(self, video_file: str, timestamp: str) -> Path:
        """Create a timestamped package directory"""
        package_name = f"video_package_{timestamp}"
        package_dir = self.DEFAULT_OUTPUT_DIR / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        return package_dir

    def mix_and_package(
        self,
        video_file: str,
        audio_file: str,
        mode: str = "replace"
    ):
        """Mix video and audio, then create upload package"""
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create package directory
        package_dir = self.create_video_package(video_file, timestamp)
        
        print(f"\n{'='*60}")
        print(f"MIXING AND PACKAGING")
        print('='*60)
        print(f"Package: {package_dir.name}")
        print(f"Video: {Path(video_file).name}")
        print(f"Audio: {Path(audio_file).name}")
        print(f"Mode: {mode.upper()}")
        print('='*60 + "\n")
        
        # Output file in package
        output_file = package_dir / "video.mp4"
        
        # Get durations
        video_duration = self.get_duration(video_file)
        audio_duration = self.get_duration(audio_file)
        
        print(f"Video duration: {video_duration:.2f}s")
        print(f"Audio duration: {audio_duration:.2f}s")
        
        if abs(video_duration - audio_duration) > 1.0:
            print(f"⚠ Duration mismatch: {abs(video_duration - audio_duration):.2f}s difference")
        
        # Mix command
        print("\nMixing video and audio...")
        
        if mode == "replace":
            cmd = [
                "ffmpeg",
                "-i", video_file,
                "-i", audio_file,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "320k",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                "-y",
                str(output_file)
            ]
        elif mode == "mix":
            cmd = [
                "ffmpeg",
                "-i", video_file,
                "-i", audio_file,
                "-filter_complex",
                "[0:a]volume=0.3[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=shortest[audio]",
                "-map", "0:v:0",
                "-map", "[audio]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "320k",
                "-y",
                str(output_file)
            ]
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        subprocess.run(cmd, capture_output=True, check=True)
        print("✓ Mixed successfully!")
        
        # Get output file size
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"✓ Output size: {file_size_mb:.1f} MB")
        
        print(f"\n{'='*60}")
        print("✓ PACKAGE CREATED")
        print('='*60)
        print(f"Location: {package_dir}")
        print(f"Video: {output_file.name}")
        print("\nNext steps:")
        print(f"  1. Add title.txt to: {package_dir}")
        print(f"  2. Add description.txt to: {package_dir}")
        print(f"  3. Add tags.txt to: {package_dir}")
        print(f"  4. Add thumbnail.png to: {package_dir}")
        print('='*60 + "\n")
        
        return package_dir

    def auto_find_files(self):
        """Find first video and audio files automatically"""
        from glob import glob
        
        video_files = sorted(glob(str(self.DEFAULT_VIDEO_DIR / "*.mp4")))
        audio_files = []
        for ext in ("*.mp3", "*.wav", "*.m4a"):
            audio_files.extend(glob(str(self.DEFAULT_AUDIO_DIR / ext)))
        
        return (video_files[0] if video_files else None, 
                audio_files[0] if audio_files else None)


def main():
    parser = argparse.ArgumentParser(description="Mix video/audio and create upload package")
    parser.add_argument("-v", "--video", help="Input video file")
    parser.add_argument("-a", "--audio", help="Input audio file")
    parser.add_argument("--mode", choices=["replace", "mix"], default="replace",
                       help="Mixing mode (default: replace)")
    args = parser.parse_args()

    mixer = MediaMixer()

    # Auto-discover files if not provided
    video = args.video
    audio = args.audio
    
    if not video or not audio:
        print("🔍 Searching for default files...")
        video, audio = mixer.auto_find_files()
        if not video or not audio:
            print("❌ No default video/audio files found.")
            print(f"   Video dir: {mixer.DEFAULT_VIDEO_DIR}")
            print(f"   Audio dir: {mixer.DEFAULT_AUDIO_DIR}")
            sys.exit(1)
        print(f"✓ Found video: {Path(video).name}")
        print(f"✓ Found audio: {Path(audio).name}")

    # Validate files exist
    if not Path(video).exists():
        print(f"❌ Video not found: {video}")
        sys.exit(1)
    if not Path(audio).exists():
        print(f"❌ Audio not found: {audio}")
        sys.exit(1)

    # Mix and create package
    try:
        package_dir = mixer.mix_and_package(video, audio, mode=args.mode)
        print(f"✅ Done! Package created at: {package_dir}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
