#!/usr/bin/env python3
"""
Video Music Indexer
Adds background music to video clips with configurable volume (default 15%)
Handles videos with or without existing audio streams
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse


class VideoMusicIndexer:
    # Default paths
    DEFAULT_INPUT_DIR = Path("../../in_production_content/videos_with_subtitles")
    DEFAULT_MUSIC_DIR = Path("../../in_production_content/downloaded_music")
    DEFAULT_OUTPUT_DIR = Path("../../in_production_content/videos_with_music")
    
    def __init__(self, input_dir=None, music_file=None, output_dir=None, music_volume=0.05):
        """
        Initialize with default or custom paths.
        
        Args:
            input_dir: Directory containing input videos
            music_file: Path to background music file
            output_dir: Output directory
            music_volume: Music volume level 0.0-1.0 (default: 0.15 = 15%)
        """
        # Create default directories
        self.DEFAULT_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_MUSIC_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Set input directory
        self.input_dir = Path(input_dir) if input_dir else self.DEFAULT_INPUT_DIR
        
        # Set music file
        if music_file:
            self.music_file = Path(music_file)
        else:
            # Find first .mp3 file in music directory
            music_files = list(self.DEFAULT_MUSIC_DIR.glob("*.mp3"))
            if music_files:
                self.music_file = music_files[0]
                print(f"Using music: {self.music_file.name}")
            else:
                self.music_file = self.DEFAULT_MUSIC_DIR / "background_music.mp3"
                print(f"⚠ No music files found in {self.DEFAULT_MUSIC_DIR}")
        
        # Set output directory
        self.output_dir = Path(output_dir) if output_dir else self.DEFAULT_OUTPUT_DIR
        self.music_volume = music_volume
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ FFmpeg is not installed or not in PATH")
            return False
    
    def has_audio_stream(self, video_file):
        """Check if video has an audio stream using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_type",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_file)
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip() == "audio"
        except Exception:
            return False
    
    def get_video_duration(self, video_file):
        """Get video duration in seconds using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_file)
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"      ✗ Error getting duration: {e}")
            return 0
    
    def add_music_to_video(self, video_file, output_file, video_number):
        """Add background music to video with configurable volume."""
        video_name = video_file.stem
        duration = self.get_video_duration(video_file)
        
        if duration == 0:
            print(f"  [{video_number}] ✗ Cannot process: {video_name}")
            return False
        
        # Check if video has audio
        has_audio = self.has_audio_stream(video_file)
        
        print(f"  [{video_number}] Adding music to: {video_name}")
        print(f"      Duration: {duration:.1f}s | Music: {int(self.music_volume * 100)}% | Has audio: {has_audio}")
        
        try:
            if has_audio:
                # Video HAS audio - mix it with background music
                print(f"      Mode: Mixing video audio + background music")
                cmd = [
                    "ffmpeg",
                    "-i", str(video_file),
                    "-i", str(self.music_file),
                    "-filter_complex",
                    f"[1:a]volume={self.music_volume}[music];[0:a][music]amix=inputs=2:duration=first[audio]",
                    "-map", "0:v",
                    "-map", "[audio]",
                    "-shortest",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-y",
                    str(output_file)
                ]
            else:
                # Video has NO audio - just add background music
                print(f"      Mode: Adding background music only (no original audio)")
                cmd = [
                    "ffmpeg",
                    "-i", str(video_file),
                    "-i", str(self.music_file),
                    "-filter_complex",
                    f"[1:a]volume={self.music_volume}[audio]",
                    "-map", "0:v",
                    "-map", "[audio]",
                    "-shortest",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-y",
                    str(output_file)
                ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0 and output_file.exists():
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"      ✓ Success! ({file_size_mb:.1f} MB)")
                return True
            else:
                print(f"      ✗ Failed (exit code: {result.returncode})")
                if result.stderr:
                    error_lines = result.stderr.strip().split('\n')
                    print(f"      Error (last 5 lines):")
                    for line in error_lines[-5:]:
                        print(f"        {line}")
                return False
        
        except Exception as e:
            print(f"      ✗ Error: {e}")
            return False
    
    def process_all_videos(self):
        """Process all video files in input directory."""
        print(f"\n[1/2] Processing videos from: {self.input_dir}")
        
        if not self.input_dir.exists():
            print(f"✗ Input directory not found: {self.input_dir}")
            return False
        
        if not self.music_file.exists():
            print(f"✗ Music file not found: {self.music_file}")
            print(f"  Please place a .mp3 file in: {self.DEFAULT_MUSIC_DIR}")
            return False
        
        video_files = sorted(self.input_dir.glob("*.mp4"))
        
        if not video_files:
            print(f"✗ No .mp4 files found in {self.input_dir}")
            return False
        
        print(f"✓ Found {len(video_files)} video files")
        
        successful = 0
        failed = 0
        
        for idx, video_file in enumerate(video_files, 1):
            output_file = self.output_dir / video_file.name
            
            if self.add_music_to_video(video_file, output_file, idx):
                successful += 1
            else:
                failed += 1
        
        print(f"\n  Summary: {successful} successful, {failed} failed")
        return failed == 0
    
    def run(self):
        """Run the full music indexing pipeline."""
        print("=" * 70)
        print("VIDEO MUSIC INDEXER")
        print("=" * 70)
        print(f"Settings:")
        print(f"  Input:  {self.input_dir}")
        print(f"  Music:  {self.music_file.name if self.music_file.exists() else 'NOT FOUND'}")
        print(f"  Volume: {int(self.music_volume * 100)}%")
        print(f"  Output: {self.output_dir}")
        
        # Check FFmpeg
        if not self.check_ffmpeg():
            return False
        
        # Process all videos
        if not self.process_all_videos():
            return False
        
        print(f"\n[2/2] Finalizing...")
        print("\n" + "=" * 70)
        print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nOutput: {self.output_dir.absolute()}")
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add background music to videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use defaults (15% music volume)
  python video_music_mixer.py
  
  # Custom music volume (30%)
  python video_music_mixer.py --volume 0.3
  
  # Quiet background (5%)
  python video_music_mixer.py --volume 0.05

Default Paths:
  Input:  ../../in_production_content/videos_with_subtitles
  Music:  ../../in_production_content/downloaded_music
  Output: ../../Post_production_content/final_videos
        """
    )
    
    parser.add_argument('--input', '-i', help='Input directory')
    parser.add_argument('--music', '-m', help='Music file (.mp3)')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--volume', '-v', type=float, default=0.01,
                       help='Music volume 0.0-1.0 (default: 0.01)')
    
    args = parser.parse_args()
    
    # Validate volume
    if not 0.0 <= args.volume <= 1.0:
        print("Error: Volume must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)
    
    # Run
    indexer = VideoMusicIndexer(
        input_dir=args.input,
        music_file=args.music,
        output_dir=args.output,
        music_volume=args.volume
    )
    
    success = indexer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
