#!/usr/bin/env python3
"""
Video Quality Enhancer
Enhance video quality using FFmpeg with multiple filters and optimization techniques
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
    
    # Default paths - modify these to your preferences
    DEFAULT_INPUT_DIR = Path("../../Pre_production_content/videos")
    DEFAULT_OUTPUT_DIR = Path("../../Post_production_content/videos")
    
    def __init__(self):
        """Initialize video enhancer"""
        self.check_ffmpeg()
        # Create default directories if they don't exist
        self.DEFAULT_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def check_ffmpeg(self):
        """Verify FFmpeg is installed"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
            subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "FFmpeg/FFprobe not found. Install it:\n"
                "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  Fedora: sudo dnf install ffmpeg\n"
                "  macOS: brew install ffmpeg"
            )
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get video information using FFprobe"""
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_streams',
                    '-show_format',
                    video_path
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'video'),
                None
            )
            audio_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'audio'),
                None
            )
            
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
        denoise: bool = True,
        sharpen: bool = True,
        upscale: bool = False,
        color_enhance: bool = True,
        bitrate: Optional[str] = None,
        fps: Optional[int] = None,
        resolution: Optional[str] = None
    ):
        """
        Enhance video quality
        
        Args:
            input_path: Input video file
            output_path: Output video file
            preset: 'light', 'balanced', 'heavy', 'extreme'
            denoise: Apply denoising filter
            sharpen: Apply sharpening filter
            upscale: Upscale video resolution
            color_enhance: Enhance colors
            bitrate: Target bitrate (e.g., '10M', '5000k')
            fps: Target frame rate
            resolution: Target resolution (e.g., '1920x1080')
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Video not found: {input_path}")
        
        print(f"\n{'='*60}")
        print("VIDEO QUALITY ENHANCEMENT")
        print('='*60)
        
        # Get video info
        print(f"\n[1/3] Analyzing video: {input_path.name}")
        video_info = self.get_video_info(str(input_path))
        print(f"✓ Resolution: {video_info['width']}x{video_info['height']}")
        print(f"✓ FPS: {video_info['fps']:.2f}")
        print(f"✓ Duration: {video_info['duration']:.1f}s")
        print(f"✓ Video Codec: {video_info['codec']}")
        print(f"✓ Bitrate: {video_info['bitrate']/1000000:.2f} Mbps")
        
        # Build video filter chain
        print(f"\n[2/3] Building enhancement filters")
        filters = self._build_filter_chain(
            preset=preset,
            denoise=denoise,
            sharpen=sharpen,
            upscale=upscale,
            color_enhance=color_enhance,
            resolution=resolution,
            original_width=video_info['width'],
            original_height=video_info['height']
        )
        
        print(f"Enhancements: {preset.upper()}")
        if denoise:
            print(f"  ✓ Denoising")
        if sharpen:
            print(f"  ✓ Sharpening")
        if upscale:
            print(f"  ✓ Upscaling")
        if color_enhance:
            print(f"  ✓ Color enhancement")
        if resolution:
            print(f"  ✓ Resolution: {resolution}")
        if fps:
            print(f"  ✓ FPS: {fps}")
        
        # Build FFmpeg command
        print(f"\n[3/3] Encoding enhanced video")
        cmd = ['ffmpeg', '-i', str(input_path)]
        
        # Add video filters
        if filters:
            cmd.extend(['-vf', filters])
        
        # Video codec options
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'slow',  # High quality
            '-crf', '18',  # High quality (0-51, lower is better)
        ])
        
        # Bitrate (if specified)
        if bitrate:
            cmd.extend(['-b:v', bitrate])
        else:
            # Auto bitrate based on resolution
            if resolution:
                w, h = map(int, resolution.split('x'))
                if w >= 3840:  # 4K
                    cmd.extend(['-b:v', '15M'])
                elif w >= 1920:  # 1080p
                    cmd.extend(['-b:v', '8M'])
                elif w >= 1280:  # 720p
                    cmd.extend(['-b:v', '5M'])
                else:
                    cmd.extend(['-b:v', '3M'])
        
        # Frame rate (if specified)
        if fps:
            cmd.extend(['-r', str(fps)])
        
        # Audio codec
        cmd.extend([
            '-c:a', 'aac',
            '-b:a', '320k'
        ])
        
        # Output options
        cmd.extend(['-y', str(output_path)])
        
        # Run FFmpeg
        try:
            print("Processing video...")
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
    
    def _build_filter_chain(
        self,
        preset: str = 'balanced',
        denoise: bool = True,
        sharpen: bool = True,
        upscale: bool = False,
        color_enhance: bool = True,
        resolution: Optional[str] = None,
        original_width: int = 1920,
        original_height: int = 1080
    ) -> str:
        """Build FFmpeg video filter chain"""
        
        filters = []
        
        # Denoising (removes noise/compression artifacts)
        if denoise:
            if preset == 'light':
                filters.append('hqdn3d=2:1:2:2')
            elif preset == 'balanced':
                filters.append('hqdn3d=4:3:6:4.5')
            elif preset == 'heavy':
                filters.append('hqdn3d=6:4:8:6')
            elif preset == 'extreme':
                filters.append('hqdn3d=8:5:10:8,nlmeans=s=1:p=7:r=15')
        
        # Color enhancement
        if color_enhance:
            if preset == 'light':
                filters.append('eq=contrast=1.05:brightness=0.01:saturation=1.05')
            elif preset == 'balanced':
                filters.append('eq=contrast=1.1:brightness=0.02:saturation=1.1')
            elif preset == 'heavy':
                filters.append('eq=contrast=1.15:brightness=0.03:saturation=1.15')
            elif preset == 'extreme':
                filters.append('eq=contrast=1.2:brightness=0.05:saturation=1.2')
        
        # Resolution upscaling
        if resolution:
            filters.append(f'scale={resolution}:flags=lanczos')
        elif upscale and original_width < 1920:
            # Auto-upscale low-res videos
            if original_width < 1280:
                filters.append('scale=1280:720:flags=lanczos')
            else:
                filters.append('scale=1920:1080:flags=lanczos')
        
        # Sharpening (enhances detail)
        if sharpen:
            if preset == 'light':
                filters.append('unsharp=3:3:0.5:3:3:0.0')
            elif preset == 'balanced':
                filters.append('unsharp=5:5:1.0:5:5:0.0')
            elif preset == 'heavy':
                filters.append('unsharp=7:7:1.5:7:7:0.0')
            elif preset == 'extreme':
                filters.append('unsharp=9:9:2.0:9:9:0.0,cas=strength=1')
        
        return ','.join(filters) if filters else ''
    
    def batch_enhance(
        self,
        input_dir: str,
        output_dir: str,
        pattern: str = '*.mp4',
        **kwargs
    ) -> list:
        """
        Batch enhance multiple videos
        
        Args:
            input_dir: Directory with input videos
            output_dir: Directory to save enhanced videos
            pattern: File pattern to match (default: *.mp4)
            **kwargs: Additional arguments passed to enhance_video
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all matching files
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
                results.append({
                    'input': str(video_file),
                    'output': str(output_file),
                    'status': 'success'
                })
            except Exception as e:
                print(f"✗ Failed: {str(e)}\n")
                results.append({
                    'input': str(video_file),
                    'output': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
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
    parser = argparse.ArgumentParser(
        description="Enhance video quality using FFmpeg",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic enhancement (balanced preset) - uses default input/output paths
  python video_quality_enhancer.py
  
  # Light enhancement with default paths
  python video_quality_enhancer.py --preset light
  
  # Heavy enhancement with custom input file
  python video_quality_enhancer.py --input video.mp4 --output enhanced.mp4
  
  # Custom output name with default input directory
  python video_quality_enhancer.py -o my_output.mp4
  
  # Upscale to 1080p with heavy enhancement
  python video_quality_enhancer.py --preset heavy --upscale --resolution 1920x1080
  
  # Custom bitrate and frame rate
  python video_quality_enhancer.py --bitrate 15M --fps 60
  
  # Batch process directory
  python video_quality_enhancer.py --batch input_dir/ output_dir/ \\
      --preset balanced

Default Paths (modify in script):
  Input:  ~/Videos/input
  Output: ~/Videos/output

Enhancement Presets:
  light    - Minimal processing (fast, good for already decent videos)
  balanced - Moderate processing (recommended, good balance)
  heavy    - Aggressive processing (slower, best quality)
  extreme  - Maximum processing (slowest, maximum quality)
        """
    )
    
    # Single file mode arguments
    parser.add_argument(
        '--input', '-i',
        help='Input video file (default: first video in input directory)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output video file (default: enhanced_[input_name] in output directory)'
    )
    
    # Batch mode
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Batch process directory'
    )
    
    parser.add_argument(
        '--pattern',
        default='*.mp4',
        help='File pattern for batch mode (default: *.mp4)'
    )
    
    # Enhancement options
    parser.add_argument(
        '--preset',
        choices=['light', 'balanced', 'heavy', 'extreme'],
        default='balanced',
        help='Enhancement preset (default: balanced)'
    )
    
    parser.add_argument(
        '--denoise',
        action='store_true',
        default=True,
        help='Apply denoising (default: enabled)'
    )
    
    parser.add_argument(
        '--no-denoise',
        action='store_false',
        dest='denoise',
        help='Disable denoising'
    )
    
    parser.add_argument(
        '--sharpen',
        action='store_true',
        default=True,
        help='Apply sharpening (default: enabled)'
    )
    
    parser.add_argument(
        '--no-sharpen',
        action='store_false',
        dest='sharpen',
        help='Disable sharpening'
    )
    
    parser.add_argument(
        '--upscale',
        action='store_true',
        help='Upscale video resolution'
    )
    
    parser.add_argument(
        '--color-enhance',
        action='store_true',
        default=True,
        help='Enhance colors (default: enabled)'
    )
    
    parser.add_argument(
        '--no-color-enhance',
        action='store_false',
        dest='color_enhance',
        help='Disable color enhancement'
    )
    
    parser.add_argument(
        '--bitrate',
        help='Target bitrate (e.g., 10M, 5000k)'
    )
    
    parser.add_argument(
        '--fps',
        type=int,
        help='Target frame rate'
    )
    
    parser.add_argument(
        '--resolution',
        help='Target resolution (e.g., 1920x1080, 1280x720)'
    )
    
    args = parser.parse_args()
    
    # Initialize enhancer
    try:
        enhancer = VideoQualityEnhancer()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Batch mode
    if args.batch:
        input_dir = args.input or str(enhancer.DEFAULT_INPUT_DIR)
        output_dir = args.output or str(enhancer.DEFAULT_OUTPUT_DIR)
        
        try:
            enhancer.batch_enhance(
                input_dir=input_dir,
                output_dir=output_dir,
                pattern=args.pattern,
                preset=args.preset,
                denoise=args.denoise,
                sharpen=args.sharpen,
                upscale=args.upscale,
                color_enhance=args.color_enhance,
                bitrate=args.bitrate,
                fps=args.fps,
                resolution=args.resolution
            )
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Single file mode
    else:
        # Get input file
        if args.input:
            input_path = Path(args.input)
        else:
            # Find first video in default input directory
            video_files = list(enhancer.DEFAULT_INPUT_DIR.glob('*.mp4')) + \
                         list(enhancer.DEFAULT_INPUT_DIR.glob('*.mkv')) + \
                         list(enhancer.DEFAULT_INPUT_DIR.glob('*.avi')) + \
                         list(enhancer.DEFAULT_INPUT_DIR.glob('*.mov'))
            
            if not video_files:
                print(f"Error: No video files found in {enhancer.DEFAULT_INPUT_DIR}", file=sys.stderr)
                print("Please place a video file in the input directory or specify --input", file=sys.stderr)
                sys.exit(1)
            
            input_path = video_files[0]
            print(f"Using input: {input_path.name}")
        
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)
        
        # Get output file
        if args.output:
            if Path(args.output).is_absolute():
                output_path = args.output
            else:
                output_path = enhancer.DEFAULT_OUTPUT_DIR / args.output
        else:
            output_path = enhancer.DEFAULT_OUTPUT_DIR / f"enhanced_{input_path.name}"
        
        try:
            enhancer.enhance_video(
                input_path=str(input_path),
                output_path=str(output_path),
                preset=args.preset,
                denoise=args.denoise,
                sharpen=args.sharpen,
                upscale=args.upscale,
                color_enhance=args.color_enhance,
                bitrate=args.bitrate,
                fps=args.fps,
                resolution=args.resolution
            )
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
