#!/usr/bin/env python3
"""
Video Quality Enhancer - OPTIMIZED
Fixes freezing issues on long videos by using lighter filters
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict
import argparse


class VideoQualityEnhancer:
    """Enhance video quality using FFmpeg"""
    
    # Default paths
    DEFAULT_INPUT_DIR = Path("../../in_production_content/videos_with_subtitles")
    DEFAULT_OUTPUT_DIR = Path("../../in_production_content/enhanced_videos")
    
    def __init__(self):
        """Initialize video enhancer"""
        self.check_ffmpeg()
        self.DEFAULT_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def check_ffmpeg(self):
        """Verify FFmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("FFmpeg/FFprobe not found. Please install FFmpeg.")
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get video information using FFprobe"""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                 '-show_streams', '-show_format', video_path],
                capture_output=True, text=True, check=True
            )
            
            data = json.loads(result.stdout)
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)
            
            info = {
                'width': video_stream.get('width', 0) if video_stream else 0,
                'height': video_stream.get('height', 0) if video_stream else 0,
                'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0,
                'codec': video_stream.get('codec_name', 'unknown') if video_stream else 'unknown',
                'bitrate': int(video_stream.get('bit_rate', 0)) if video_stream else 0,
                'duration': float(data['format'].get('duration', 0)),
                'audio_codec': audio_stream.get('codec_name', 'unknown') if audio_stream else None,
                'audio_bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream else 0,
            }
            
            return info
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")
    
    def enhance_video(
        self,
        input_path: str,
        output_path: str,
        preset: str = 'balanced',
        bitrate: Optional[str] = None
    ):
        """
        Enhance video quality - OPTIMIZED FOR LONG VIDEOS
        Uses lighter filters to prevent freezing
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Video not found: {input_path}")
        
        print(f"\n{'='*60}")
        print("VIDEO QUALITY ENHANCEMENT (OPTIMIZED)")
        print('='*60)
        
        # Get video info
        print(f"\n[1/2] Analyzing video: {input_path.name}")
        video_info = self.get_video_info(str(input_path))
        print(f"✓ Resolution: {video_info['width']}x{video_info['height']}")
        print(f"✓ FPS: {video_info['fps']:.2f}")
        print(f"✓ Duration: {video_info['duration']:.1f}s")
        print(f"✓ Codec: {video_info['codec']}")
        
        # Build lightweight filter
        print(f"\n[2/2] Building lightweight enhancement...")
        filters = self._build_lightweight_filter(preset)
        
        print(f"Preset: {preset.upper()}")
        print("Optimizations: Fast encoding, minimal processing")
        
        # Build FFmpeg command - OPTIMIZED
        cmd = ['ffmpeg', '-i', str(input_path)]
        
        # Add video filters (if any)
        if filters:
            cmd.extend(['-vf', filters])
        
        # Video codec options - OPTIMIZED FOR SPEED
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'veryfast',  # Much faster than 'slow'
            '-crf', '23',           # Good quality, fast encoding
        ])
        
        # Bitrate
        if bitrate:
            cmd.extend(['-b:v', bitrate])
        else:
            # Auto bitrate
            w = video_info['width']
            if w >= 3840:
                cmd.extend(['-b:v', '15M'])
            elif w >= 1920:
                cmd.extend(['-b:v', '8M'])
            elif w >= 1280:
                cmd.extend(['-b:v', '5M'])
            else:
                cmd.extend(['-b:v', '3M'])
        
        # Audio codec - COPY FOR SPEED
        cmd.extend(['-c:a', 'copy'])  # No audio re-encoding
        
        # Output
        cmd.extend(['-y', str(output_path)])
        
        # Run FFmpeg
        try:
            print("\nProcessing video (optimized for speed)...")
            subprocess.run(cmd, check=True)
            print(f"\n✓ Enhanced video saved: {output_path}")
            
            # Get output info
            output_info = self.get_video_info(str(output_path))
            print(f"\nOutput Statistics:")
            print(f"  Resolution: {output_info['width']}x{output_info['height']}")
            print(f"  Bitrate: {output_info['bitrate']/1000000:.2f} Mbps")
            
            print(f"\n{'='*60}")
            print("✓ COMPLETE")
            print('='*60 + "\n")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg error: {str(e)}")
    
    def _build_lightweight_filter(self, preset: str = 'balanced') -> str:
        """Build LIGHTWEIGHT filter chain - prevents freezing"""
        filters = []
        
        # Very light color enhancement only
        if preset == 'light':
            filters.append('eq=contrast=1.02:brightness=0.01:saturation=1.02')
        elif preset == 'balanced':
            filters.append('eq=contrast=1.05:brightness=0.01:saturation=1.05')
        elif preset == 'heavy':
            filters.append('eq=contrast=1.08:brightness=0.02:saturation=1.08')
        
        # NO denoising, NO sharpening for long videos - they cause freezing
        
        return ','.join(filters) if filters else ''
    
    def batch_enhance(self, input_dir: str, output_dir: str, pattern: str = '*.mp4', **kwargs) -> list:
        """Batch enhance multiple videos"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        video_files = list(input_path.glob(pattern))
        
        print(f"\n{'='*60}")
        print(f"BATCH VIDEO ENHANCEMENT")
        print(f"{'='*60}")
        print(f"Found {len(video_files)} videos to process\n")
        
        results = []
        
        for i, video_file in enumerate(video_files, 1):
            output_file = output_path / f"enhanced_{video_file.name}"
            
            print(f"[{i}/{len(video_files)}] Processing: {video_file.name}")
            
            try:
                self.enhance_video(
                    input_path=str(video_file),
                    output_path=str(output_file),
                    **kwargs
                )
                results.append({'input': str(video_file), 'output': str(output_file), 'status': 'success'})
            except Exception as e:
                print(f"✗ Failed: {str(e)}\n")
                results.append({'input': str(video_file), 'output': None, 'status': 'failed', 'error': str(e)})
        
        # Summary
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'failed')
        
        print(f"\n{'='*60}")
        print("BATCH COMPLETE")
        print('='*60)
        print(f"Total: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print('='*60 + "\n")
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Enhance video quality (optimized for long videos)")
    parser.add_argument('--input', '-i', help='Input video file')
    parser.add_argument('--output', '-o', help='Output video file')
    parser.add_argument('--batch', action='store_true', help='Batch process directory')
    parser.add_argument('--pattern', default='*.mp4', help='File pattern for batch mode')
    parser.add_argument('--preset', choices=['light', 'balanced', 'heavy'], default='balanced')
    parser.add_argument('--bitrate', help='Target bitrate (e.g., 10M, 5000k)')
    
    args = parser.parse_args()
    
    try:
        enhancer = VideoQualityEnhancer()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    if args.batch:
        input_dir = args.input or str(enhancer.DEFAULT_INPUT_DIR)
        output_dir = args.output or str(enhancer.DEFAULT_OUTPUT_DIR)
        
        try:
            enhancer.batch_enhance(input_dir, output_dir, args.pattern, preset=args.preset, bitrate=args.bitrate)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if args.input:
            input_path = Path(args.input)
        else:
            video_files = list(enhancer.DEFAULT_INPUT_DIR.glob('*.mp4'))
            if not video_files:
                print(f"Error: No video files found in {enhancer.DEFAULT_INPUT_DIR}", file=sys.stderr)
                sys.exit(1)
            input_path = video_files[0]
            print(f"Using input: {input_path.name}")
        
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)
        
        if args.output:
            output_path = args.output if Path(args.output).is_absolute() else enhancer.DEFAULT_OUTPUT_DIR / args.output
        else:
            output_path = enhancer.DEFAULT_OUTPUT_DIR / f"enhanced_{input_path.name}"
        
        try:
            enhancer.enhance_video(str(input_path), str(output_path), preset=args.preset, bitrate=args.bitrate)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
