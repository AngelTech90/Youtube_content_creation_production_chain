#!/usr/bin/env python3
"""
Video Integration Script with FFmpeg
Directly replaces video segments at specified timestamps with complementary videos.
Simple cut-and-replace approach that preserves video duration and frame rate.
"""
import re
import os
import sys
import subprocess
import pickle
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv


def get_pkl_paths(path):
    """Get first .pkl file in directory"""
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if re.match(r'.*\.pkl$', name):
                    return os.path.join(root, name)
    except Exception as e:
        print(f"Error finding pkl file: {e}")
    return None


def get_mp4_paths(path):
    """Get first .mp4 file in directory"""
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if re.match(r'.*\.mp4$', name):
                    return os.path.join(root, name)
    except Exception as e:
        print(f"Error finding mp4 file: {e}")
    return None


class VideoIntegrator:

    # Default paths
    DEFAULT_INITIAL_VIDEO_DIR = Path("../../Pre_production_content/videos")
    DEFAULT_OUTPUT_DIR = Path("../../in_production_content/mixed_videos")
    DEFAULT_PKL_DICT = Path("../../Core_data_workflow/data_sets")
    DEFAULT_COMPLEMENTARY_VIDEOS = Path("../../in_production_content/complementary_videos")

    def __init__(self, gemini_api_key, original_video=None, pkl_file=None, complementary_dir=None):
        """Initialize the video integrator."""
        # Create default directories
        self.DEFAULT_INITIAL_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_PKL_DICT.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_COMPLEMENTARY_VIDEOS.mkdir(parents=True, exist_ok=True)
        
        # Configure Gemini API
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Set original video
        if original_video:
            self.original_video = Path(original_video)
        else:
            video_file = get_mp4_paths(str(self.DEFAULT_INITIAL_VIDEO_DIR))
            if video_file:
                self.original_video = Path(video_file)
                print(f"Using original video: {self.original_video.name}")
            else:
                raise FileNotFoundError(
                    f"No .mp4 files found in {self.DEFAULT_INITIAL_VIDEO_DIR}"
                )
        
        # Set pickle file
        if pkl_file:
            self.pkl_file = Path(pkl_file)
        else:
            pkl_path = get_pkl_paths(str(self.DEFAULT_PKL_DICT))
            if pkl_path:
                self.pkl_file = Path(pkl_path)
                print(f"Using pickle file: {self.pkl_file.name}")
            else:
                raise FileNotFoundError(
                    f"No .pkl files found in {self.DEFAULT_PKL_DICT}"
                )
        
        # Set complementary directory
        if complementary_dir:
            self.complementary_dir = Path(complementary_dir)
        else:
            self.complementary_dir = self.DEFAULT_COMPLEMENTARY_VIDEOS
        
        # Output directory
        self.output_dir = self.DEFAULT_OUTPUT_DIR
        
        # Data containers
        self.timestamps_data = {}
        self.video_files = []
        self.sorted_videos = []
        self.video_durations = []
        self.video_fps = None
        self.video_resolution = None
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            print("✓ FFmpeg is installed and accessible")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ FFmpeg is not installed or not in PATH")
            return False
    
    def load_timestamps(self):
        """Load timestamp data from pickle file."""
        print(f"\n[1/6] Loading timestamp data from: {self.pkl_file}")
        
        if not self.pkl_file.exists():
            raise FileNotFoundError(f"Pickle file not found: {self.pkl_file}")
        
        try:
            with open(self.pkl_file, 'rb') as f:
                self.timestamps_data = pickle.load(f)
            
            print(f"✓ Loaded {len(self.timestamps_data)} timestamp entries")
            print("\nTimestamp entries:")
            for idx, (key, timestamps) in enumerate(self.timestamps_data.items(), 1):
                start, end = timestamps
                duration = self._timestamp_to_seconds(end) - self._timestamp_to_seconds(start)
                print(f"  {idx}. {key}: {timestamps[0]} → {timestamps[1]} ({duration:.1f}s)")
            
            return True
        except Exception as e:
            print(f"✗ Error loading pickle file: {e}")
            return False
    
    def extract_video_files(self):
        """Extract list of video files from complementary directory."""
        print(f"\n[2/6] Extracting video files from: {self.complementary_dir}")
        
        if not self.complementary_dir.exists():
            print(f"✗ Directory not found: {self.complementary_dir}")
            return False
        
        self.video_files = sorted([f.name for f in self.complementary_dir.glob("*.mp4")])
        
        if not self.video_files:
            print("✗ No .mp4 files found in directory")
            return False
        
        print(f"✓ Found {len(self.video_files)} video files")
        return True
    
    def sort_videos_with_gemini(self):
        """Use Gemini to match and sort video files with timestamp keys."""
        print(f"\n[3/6] Matching videos with timestamps using Gemini AI...")
        
        timestamp_keys = list(self.timestamps_data.keys())
        
        prompt = f"""Match video filenames with timestamp keys and return them in order.

Timestamp Keys (in order):
{json.dumps(timestamp_keys, indent=2)}

Video Filenames:
{json.dumps(self.video_files, indent=2)}

Return ONLY a Python list of video filenames matching the timestamp order.
Example: ["01_first.mp4", "02_second.mp4"]

List:"""
        
        try:
            response = self.model.generate_content(prompt)
            self.sorted_videos = self._extract_list(response.text.strip())
            
            if self.sorted_videos and len(self.sorted_videos) == len(timestamp_keys):
                print(f"✓ Successfully sorted {len(self.sorted_videos)} videos")
                return True
            else:
                print("✗ Failed to sort videos properly")
                return False
                
        except Exception as e:
            print(f"✗ Error sorting videos: {e}")
            return False
    
    def remove_audio_from_original(self):
        """Remove all audio from original video before processing."""
        print(f"\n[4/7] Removing audio from original video...")
        
        silent_video = self.output_dir / f"silent_{self.original_video.name}"
        
        # Skip if already processed
        if silent_video.exists():
            print(f"  ✓ Silent video already exists: {silent_video.name}")
            self.original_video = silent_video
            return True
        
        try:
            cmd = [
                "ffmpeg", "-i", str(self.original_video),
                "-an",  # Remove all audio streams
                "-c:v", "copy",  # Copy video without re-encoding
                "-y", str(silent_video)
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0 and silent_video.exists():
                print(f"  ✓ Audio removed successfully")
                print(f"  Silent video: {silent_video.name}")
                self.original_video = silent_video  # Use silent video from now on
                return True
            else:
                print(f"  ✗ Failed to remove audio")
                print(result.stderr[-500:])
                return False
                
        except Exception as e:
            print(f"  ✗ Error removing audio: {e}")
            return False
    
    def get_video_properties(self):
        """Get original video properties (FPS, resolution)."""
        print(f"\n[5/7] Getting video properties...")
        
        try:
            # Get FPS
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(self.original_video)
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            fps_str = result.stdout.strip()
            num, den = map(int, fps_str.split('/'))
            self.video_fps = num / den
            
            # Get resolution
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                str(self.original_video)
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            self.video_resolution = result.stdout.strip()
            
            print(f"  Original video FPS: {self.video_fps:.2f}")
            print(f"  Original video resolution: {self.video_resolution}")
            print("✓ Video properties extracted")
            return True
            
        except Exception as e:
            print(f"✗ Error getting video properties: {e}")
            return False
    
    def scale_complementary_videos(self):
        """Scale complementary videos to match original video properties."""
        print(f"\n[6/7] Scaling complementary videos to match original...")
        
        scaled_dir = self.complementary_dir / "scaled"
        scaled_dir.mkdir(exist_ok=True)
        
        for idx, video_name in enumerate(self.sorted_videos, 1):
            video_path = self.complementary_dir / video_name
            scaled_path = scaled_dir / video_name
            
            # Skip if already scaled
            if scaled_path.exists():
                print(f"  {idx}. {video_name}: Already scaled")
                continue
            
            print(f"  {idx}. {video_name}: Scaling...")
            
            try:
                cmd = [
                    "ffmpeg", "-i", str(video_path),
                    "-vf", f"scale={self.video_resolution},fps={self.video_fps}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-an",  # Remove audio from complementary videos
                    "-y", str(scaled_path)
                ]
                
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result.returncode == 0:
                    print(f"    ✓ Scaled successfully")
                else:
                    print(f"    ✗ Scaling failed")
                    return False
                    
            except Exception as e:
                print(f"    ✗ Error: {e}")
                return False
        
        # Update to use scaled videos
        self.complementary_dir = scaled_dir
        print("✓ All videos scaled successfully")
        return True
    
    def integrate_videos_direct_replace(self):
        """Integrate videos using fast segment cut-and-replace method."""
        print(f"\n[7/7] Integrating videos using fast segment replacement...")
        
        temp_dir = tempfile.mkdtemp(prefix='video_integration_')
        print(f"  Using temp directory: {temp_dir}")
        
        try:
            timestamp_keys = list(self.timestamps_data.keys())
            segments = []
            
            # Get original video duration
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(self.original_video)
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
            original_duration = float(result.stdout.strip())
            
            print(f"  Original video duration: {original_duration:.2f}s")
            print(f"  Creating segment plan...")
            
            # Build segment plan
            last_end = 0.0
            
            for idx, key in enumerate(timestamp_keys):
                start, end = self.timestamps_data[key]
                start_sec = self._timestamp_to_seconds(start)
                end_sec = self._timestamp_to_seconds(end)
                
                # Add main video segment BEFORE this replacement (if any)
                if start_sec > last_end:
                    segments.append({
                        'type': 'main',
                        'start': last_end,
                        'end': start_sec,
                        'duration': start_sec - last_end,
                        'index': len(segments)
                    })
                    print(f"    Segment {len(segments)}: Main video {last_end:.2f}s → {start_sec:.2f}s ({start_sec - last_end:.2f}s)")
                
                # Add complementary video replacement
                segments.append({
                    'type': 'complementary',
                    'video': self.sorted_videos[idx],
                    'duration': end_sec - start_sec,
                    'index': len(segments)
                })
                print(f"    Segment {len(segments)}: {self.sorted_videos[idx]} ({end_sec - start_sec:.2f}s)")
                
                last_end = end_sec
            
            # Add final main video segment (if any)
            if last_end < original_duration:
                segments.append({
                    'type': 'main',
                    'start': last_end,
                    'end': original_duration,
                    'duration': original_duration - last_end,
                    'index': len(segments)
                })
                print(f"    Segment {len(segments)}: Main video {last_end:.2f}s → {original_duration:.2f}s ({original_duration - last_end:.2f}s)")
            
            print(f"  ✓ Created {len(segments)} segments")
            
            # Calculate expected total duration
            expected_duration = sum(seg['duration'] for seg in segments)
            print(f"  Expected total duration: {expected_duration:.2f}s")
            
            # Extract main video segments using ACCURATE seeking
            print(f"  Extracting main video segments...")
            main_segments_extracted = 0
            
            for seg in segments:
                if seg['type'] == 'main':
                    output = Path(temp_dir) / f"seg_{seg['index']:03d}.mp4"
                    
                    # Use accurate seeking: -ss AFTER -i for precise cuts
                    cmd = [
                        "ffmpeg", "-v", "quiet",
                        "-i", str(self.original_video),
                        "-ss", str(seg['start']),
                        "-to", str(seg['end']),
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                        "-y", str(output)
                    ]
                    
                    result = subprocess.run(cmd)
                    if result.returncode != 0:
                        print(f"    ✗ Failed to extract segment {seg['index']}")
                        return False
                    
                    seg['file'] = output
                    main_segments_extracted += 1
                    
                    # Verify segment duration
                    verify_cmd = [
                        "ffprobe", "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        str(output)
                    ]
                    verify_result = subprocess.run(verify_cmd, stdout=subprocess.PIPE, text=True)
                    actual_duration = float(verify_result.stdout.strip())
                    print(f"    Main segment {seg['index']}: Expected {seg['duration']:.2f}s, Got {actual_duration:.2f}s")
            
            print(f"    ✓ Extracted {main_segments_extracted} main video segments")
            
            # Copy complementary videos (already scaled and correct duration)
            print(f"  Preparing complementary videos...")
            comp_segments_prepared = 0
            
            for seg in segments:
                if seg['type'] == 'complementary':
                    source = self.complementary_dir / seg['video']
                    output = Path(temp_dir) / f"seg_{seg['index']:03d}.mp4"
                    
                    # Re-encode to ensure compatibility with concat
                    cmd = [
                        "ffmpeg", "-v", "quiet",
                        "-i", str(source),
                        "-t", str(seg['duration']),
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                        "-y", str(output)
                    ]
                    
                    result = subprocess.run(cmd)
                    if result.returncode != 0:
                        print(f"    ✗ Failed to prepare segment {seg['index']}")
                        return False
                    
                    seg['file'] = output
                    comp_segments_prepared += 1
                    
                    # Verify segment duration
                    verify_cmd = [
                        "ffprobe", "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        str(output)
                    ]
                    verify_result = subprocess.run(verify_cmd, stdout=subprocess.PIPE, text=True)
                    actual_duration = float(verify_result.stdout.strip())
                    print(f"    Comp segment {seg['index']}: Expected {seg['duration']:.2f}s, Got {actual_duration:.2f}s")
            
            print(f"    ✓ Prepared {comp_segments_prepared} complementary videos")
            
            # Create concat list
            print(f"  Creating concatenation list...")
            concat_file = Path(temp_dir) / "concat_list.txt"
            
            with open(concat_file, 'w') as f:
                for seg in segments:
                    # Escape single quotes in path
                    path_str = str(seg['file']).replace("'", "'\\''")
                    f.write(f"file '{path_str}'\n")
            
            print(f"    ✓ Concat list with {len(segments)} segments")
            
            # Debug: Show concat list
            print(f"\n  Concat list contents:")
            with open(concat_file, 'r') as f:
                for i, line in enumerate(f, 1):
                    print(f"    {i}. {line.strip()}")
            
            # Prepare output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"final_video_{timestamp}.mp4"
            
            # Concatenate all segments
            print(f"\n  Concatenating segments...")
            
            cmd = [
                "ffmpeg", "-v", "error",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                "-y", str(output_file)
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0 and output_file.exists():
                print(f"✓ Video integration completed successfully!")
                print(f"  Output: {output_file}")
                
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"  Size: {file_size_mb:.2f} MB")
                
                # Verify output duration
                cmd = [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(output_file)
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
                output_duration = float(result.stdout.strip())
                
                print(f"\n  Duration verification:")
                print(f"    Original video: {original_duration:.2f}s")
                print(f"    Expected output: {expected_duration:.2f}s")
                print(f"    Actual output: {output_duration:.2f}s")
                
                if abs(output_duration - expected_duration) < 2.0:
                    print("  ✓ Duration is correct!")
                else:
                    print(f"  ⚠ Duration difference: {abs(output_duration - expected_duration):.2f}s")
                
                return True
            else:
                print("✗ Video integration failed")
                print("\nFFmpeg error:")
                print(result.stderr)
                return False
            
        except Exception as e:
            print(f"✗ Error during integration: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Keep temp files for debugging
            print(f"\n  Temp directory kept for inspection: {temp_dir}")
            print(f"  (Delete manually when done: rm -rf {temp_dir})")
    
    def _timestamp_to_seconds(self, timestamp):
        """Convert timestamp string to seconds."""
        parts = timestamp.split(':')
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    
    def _extract_list(self, text):
        """Extract Python list from AI response text."""
        text = re.sub(r'```python\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        try:
            result = eval(text)
            if isinstance(result, list):
                return result
        except:
            pass
        
        list_pattern = r'\[.*?\]'
        matches = re.finditer(list_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                potential_list = eval(match.group())
                if isinstance(potential_list, list):
                    return potential_list
            except:
                continue
        
        return None
    
    def run_full_pipeline(self):
        """Execute the complete integration pipeline."""
        print("=" * 70)
        print("Direct Replace Video Integration - FFmpeg + Gemini AI")
        print("=" * 70)
        
        if not self.check_ffmpeg():
            return False
        
        if not self.load_timestamps():
            return False
        
        if not self.extract_video_files():
            return False
        
        if not self.sort_videos_with_gemini():
            return False
        
        if not self.remove_audio_from_original():
            return False
        
        if not self.get_video_properties():
            return False
        
        if not self.scale_complementary_videos():
            return False
        
        if not self.integrate_videos_direct_replace():
            return False
        
        print("\n" + "=" * 70)
        print("✓ Pipeline completed successfully!")
        print("=" * 70)
        
        return True


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("Direct Replace Video Integration Script")
    print("=" * 70 + "\n")
    
    load_dotenv()
    
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)
    
    original_video = sys.argv[1] if len(sys.argv) > 1 else None
    pkl_file = sys.argv[2] if len(sys.argv) > 2 else None
    complementary_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        integrator = VideoIntegrator(
            gemini_api_key,
            original_video,
            pkl_file,
            complementary_dir
        )
        success = integrator.run_full_pipeline()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
