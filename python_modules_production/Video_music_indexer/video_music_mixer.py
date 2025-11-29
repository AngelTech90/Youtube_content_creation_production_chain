#!/usr/bin/env python3
"""
Video Music Indexer
Adds background music to video clips with configurable volume (default 15%)
"""

import os
import sys
import subprocess
from pathlib import Path


class VideoMusicIndexer:
    def __init__(self):
        """Initialize with default paths."""
        self.input_dir = Path("youtube_shorts_clips")
        self.music_file = Path("background_music.mp3")
        self.output_dir = Path("youtube_shorts_with_music")
        self.music_volume = 0.15  # 15% default volume
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
    
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
        """Add background music to video with 15% volume."""
        video_name = video_file.stem
        duration = self.get_video_duration(video_file)
        
        if duration == 0:
            print(f"  [{video_number}] ✗ Cannot process: {video_name}")
            return False
        
        print(f"  [{video_number}] Adding music to: {video_name}")
        print(f"      Duration: {duration:.1f}s | Music volume: {int(self.music_volume * 100)}%")
        
        try:
            # FFmpeg command to add music with volume adjustment
            # Music volume at 15% (0.15)
            # Video audio kept at full volume
            cmd = [
                "ffmpeg",
                "-i", str(video_file),
                "-i", str(self.music_file),
                "-filter_complex",
                f"[1:a]volume={self.music_volume}[music];[0:a][music]amix=inputs=2:duration=first[audio]",
                "-map", "0:v",
                "-map", "[audio]",
                "-shortest",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-y",
                str(output_file)
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0 and output_file.exists():
                print(f"      ✓ Music added successfully")
                return True
            else:
                print(f"      ✗ Failed to add music")
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
        print("=" * 60)
        print("Video Music Indexer")
        print("=" * 60)
        print(f"Settings:")
        print(f"  Input directory: {self.input_dir}")
        print(f"  Music file: {self.music_file}")
        print(f"  Music volume: {int(self.music_volume * 100)}%")
        print(f"  Output directory: {self.output_dir}")
        
        # Process all videos
        if not self.process_all_videos():
            return False
        
        print(f"\n[2/2] Finalizing...")
        print("\n" + "=" * 60)
        print("✓ Pipeline completed successfully!")
        print("=" * 60)
        print(f"\nOutput directory: {self.output_dir.absolute()}")
        
        return True


def main():
    """Main entry point."""
    indexer = VideoMusicIndexer()
    success = indexer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
