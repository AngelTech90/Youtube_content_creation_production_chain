#!/usr/bin/env python3
"""
Word-by-Word Subtitle Generator
Shows each word individually for maximum impact
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


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not get video duration: {e}")
        return 0.0


class GeminiTranscriptionAnalyzer:
    """Analyze transcriptions using Google Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google Gemini API key required.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def generate_word_subtitles(self, transcription_text: str, video_duration: float) -> List[Dict]:
        """
        Generate word-by-word subtitles from transcription
        Each word appears individually for maximum impact
        """
        print(f"Generating word-by-word subtitles for {video_duration:.1f}s video...")
        
        if isinstance(transcription_text, str) and len(transcription_text) < 500 and Path(transcription_text).exists():
            with open(transcription_text, 'r', encoding='utf-8') as f:
                transcription_text = f.read()
        
        print(f"  Analyzing {len(transcription_text)} characters of transcription")
        
        prompt = f"""You are a video subtitle expert. Analyze this transcription and identify 5-12 KEY MOMENTS for word-by-word emphasis.

VIDEO DURATION: {video_duration:.1f} seconds

TRANSCRIPTION:
{transcription_text}

YOUR TASK:
Select 5-12 strategic moments where individual WORDS should flash on screen for maximum impact.

SELECTION CRITERIA:
1. **Power words** - Words with emotional weight (breakthrough, amazing, critical, etc.)
2. **Key numbers/stats** - Important data points
3. **Action words** - Verbs that drive the message
4. **Core concepts** - Essential terminology
5. **Emotional peaks** - Words at climactic moments

RULES:
- Select ONLY 5-12 key moments total
- For each moment, choose 1-4 WORDS maximum
- Each word should appear for 0.4-0.6 seconds
- Space moments at least 20-30 seconds apart
- Words must be SINGLE words (no phrases)
- Timing should align with when words are actually spoken

Return ONLY valid JSON:
[
  {{
    "words": ["Limits", "don't", "exist"],
    "start": 15.0,
    "word_duration": 0.5,
    "reason": "main thesis"
  }},
  {{
    "words": ["breakthrough"],
    "start": 45.0,
    "word_duration": 0.6,
    "reason": "power word"
  }}
]

EXAMPLES OF GOOD SELECTIONS:
✓ ["incredible", "results"]
✓ ["72%", "increase"]
✓ ["game", "changer"]
✓ ["proven", "strategy"]

EXAMPLES OF BAD SELECTIONS:
✗ ["and", "then", "I", "realized", "that"] (too many words)
✗ ["the", "is", "was"] (filler words, no impact)
✗ ["basically what happened"] (phrase, not individual words)

Return only the JSON array with 5-12 strategic moments:"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON in Gemini response")
            
            json_str = json_match.group(0)
            segments = json.loads(json_str)
            
            # Validate minimum spacing
            min_gap = 20.0
            filtered = []
            last_end = -min_gap
            
            for seg in segments:
                start = seg.get('start', 0.0)
                if start - last_end >= min_gap:
                    filtered.append(seg)
                    word_count = len(seg.get('words', []))
                    duration = seg.get('word_duration', 0.5)
                    last_end = start + (word_count * duration)
            
            if len(filtered) < len(segments):
                print(f"  ⚠ Filtered {len(segments)} → {len(filtered)} moments (enforcing 20s spacing)")
                segments = filtered
            
            if len(segments) > 12:
                print(f"  ⚠ Limiting to 12 moments (had {len(segments)})")
                segments = segments[:12]
            
            print(f"✓ Generated {len(segments)} word-emphasis moments")
            
            return segments
            
        except Exception as e:
            raise Exception(f"Gemini subtitle generation failed: {str(e)}")


class WordSubtitleGenerator:
    """Generate word-by-word subtitle files"""
    
    @staticmethod
    def segments_to_individual_words(segments: List[Dict]) -> List[Dict]:
        """Convert word segments to individual word entries with timing"""
        individual_words = []
        
        for seg in segments:
            words = seg.get('words', [])
            start_time = seg.get('start', 0.0)
            word_duration = seg.get('word_duration', 0.5)
            
            for i, word in enumerate(words):
                word_start = start_time + (i * word_duration)
                word_end = word_start + word_duration
                
                individual_words.append({
                    'text': word,
                    'start': word_start,
                    'end': word_end,
                    'duration': word_duration
                })
        
        return individual_words
    
    @staticmethod
    def generate_srt(word_segments: List[Dict], output_path: str):
        """Generate SRT with individual words"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(word_segments, 1):
                start_time = WordSubtitleGenerator._seconds_to_srt_time(seg['start'])
                end_time = WordSubtitleGenerator._seconds_to_srt_time(seg['end'])
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{seg['text']}\n")
                f.write("\n")
        
        print(f"✓ SRT file: {output_path}")
    
    @staticmethod
    def generate_ass_with_fade(
        word_segments: List[Dict],
        output_path: str,
        font_name: str = "Lato-Bold",
        font_size: int = 130,
        fade_duration: float = 0.4
    ):
        """Generate ASS with word-by-word display and fade animations"""
        fade_ms = int(fade_duration * 1000)
        
        ass_content = f"""[Script Info]
Title: Word-by-Word Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,10,10,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        for seg in word_segments:
            start = WordSubtitleGenerator._seconds_to_ass_time(seg['start'])
            end = WordSubtitleGenerator._seconds_to_ass_time(seg['end'])
            text = seg['text']
            
            fade_tag = f"{{\\fad({fade_ms},{fade_ms})}}"
            ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{fade_tag}{text}\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        print(f"✓ ASS file with {fade_ms}ms fade: {output_path}")
    
    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')
    
    @staticmethod
    def _seconds_to_ass_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        centisecs = int((secs % 1) * 100)
        secs = int(secs)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"


class SubtitleInjector:
    """Inject subtitles into videos using FFmpeg"""
    
    def __init__(self, font_path: Optional[str] = None):
        self.font_path = font_path
        self.check_ffmpeg()
    
    def check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def inject_subtitles_fast(self, video_path: str, ass_path: str, output_path: str):
        """Inject ASS subtitles (optimized)"""
        video_path = Path(video_path)
        ass_path = Path(ass_path)
        output_path = Path(output_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        if not ass_path.exists():
            raise FileNotFoundError(f"ASS file not found: {ass_path}")
        
        print(f"\nInjecting word-by-word subtitles...")
        print(f"  Video: {video_path.name}")
        print(f"  Subtitles: {ass_path.name}")
        
        ass_path_str = str(ass_path.resolve()).replace('\\', '/')
        
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', f"ass='{ass_path_str}'",
            '-c:v', 'libx264',
            '-preset', 'faster',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ]
        
        print("\n" + "="*60)
        print("ENCODING VIDEO...")
        print("="*60 + "\n")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            for line in process.stdout:
                if 'frame=' in line or 'speed=' in line:
                    print(line.strip())
            
            process.wait()
            
            if process.returncode == 0 and output_path.exists():
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"\n✓ Success! Output: {output_path}")
                print(f"  File size: {file_size_mb:.1f} MB")
            else:
                raise Exception("FFmpeg encoding failed")
                
        except Exception as e:
            raise Exception(f"FFmpeg error: {str(e)}")


class WordByWordSubtitleWorkflow:
    """Complete word-by-word subtitle workflow"""
    
    DEFAULT_TRANSCRIPTION_DIR = Path("../../in_production_content/transcriptions/videos_transcriptions")
    DEFAULT_VIDEO_DIR = Path("../../Pre_production_content/videos")
    DEFAULT_OUTPUT_DIR = Path("../../in_production_content/videos_with_subtitles")
    DEFAULT_FONT_DIR = Path("../../Pre_production_content/fonts")
    
    def __init__(self, api_key: Optional[str] = None, font_path: Optional[str] = None):
        self.DEFAULT_TRANSCRIPTION_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_FONT_DIR.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = GeminiTranscriptionAnalyzer(api_key=api_key)
        self.generator = WordSubtitleGenerator()
        self.injector = SubtitleInjector(font_path=font_path)
    
    def process(
        self,
        transcription_path: Optional[str] = None,
        video_path: Optional[str] = None,
        output_video_path: Optional[str] = None,
        font_name: str = "Lato-Bold",
        font_size: int = 130,
        fade_duration: float = 0.4
    ):
        """Complete workflow"""
        if not transcription_path:
            transcription_path = get_first_file(str(self.DEFAULT_TRANSCRIPTION_DIR), '.txt')
            if not transcription_path:
                raise FileNotFoundError(f"No .txt files found in {self.DEFAULT_TRANSCRIPTION_DIR}")
            print(f"Using transcription: {Path(transcription_path).name}")
        
        if not video_path:
            video_path = get_first_file(str(self.DEFAULT_VIDEO_DIR), '.mp4')
            if not video_path:
                raise FileNotFoundError(f"No .mp4 files found in {self.DEFAULT_VIDEO_DIR}")
            print(f"Using video: {Path(video_path).name}")
        
        if not output_video_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_video_path = self.DEFAULT_OUTPUT_DIR / f"subtitled_video_{timestamp}.mp4"
        else:
            output_video_path = Path(output_video_path)
            if not output_video_path.is_absolute():
                output_video_path = self.DEFAULT_OUTPUT_DIR / output_video_path
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        srt_output = self.DEFAULT_OUTPUT_DIR / f"subtitles_{timestamp}.srt"
        ass_output = self.DEFAULT_OUTPUT_DIR / f"subtitles_{timestamp}.ass"
        
        print(f"\n{'='*70}")
        print("WORD-BY-WORD SUBTITLE WORKFLOW")
        print("Each word appears individually for maximum impact")
        print('='*70)
        
        print(f"\n[1/5] Analyzing video...")
        video_duration = get_video_duration(str(video_path))
        print(f"✓ Video duration: {video_duration:.1f} seconds")
        
        print(f"\n[2/5] Loading transcription: {Path(transcription_path).name}")
        with open(transcription_path, 'r', encoding='utf-8') as f:
            transcription_text = f.read()
        print(f"✓ Loaded {len(transcription_text)} characters")
        
        print(f"\n[3/5] Generating word-by-word moments with Gemini AI...")
        segments = self.analyzer.generate_word_subtitles(transcription_text, video_duration)
        
        print(f"\n[4/5] Creating word-by-word subtitle files...")
        word_segments = self.generator.segments_to_individual_words(segments)
        print(f"  Total words to display: {len(word_segments)}")
        
        self.generator.generate_srt(word_segments, str(srt_output))
        self.generator.generate_ass_with_fade(
            word_segments,
            str(ass_output),
            font_name=font_name,
            font_size=font_size,
            fade_duration=fade_duration
        )
        
        print(f"\n[5/5] Injecting subtitles into video...")
        self.injector.inject_subtitles_fast(
            str(video_path),
            str(ass_output),
            str(output_video_path)
        )
        
        print(f"\n{'='*70}")
        print("✓ WORKFLOW COMPLETE")
        print('='*70)
        print(f"Words displayed: {len(word_segments)}")
        print(f"Video:           {output_video_path}")
        print(f"SRT:             {srt_output}")
        print(f"ASS (styled):    {ass_output}")
        print(f"Style:           {font_name} ({font_size}px), {int(fade_duration*1000)}ms fade")
        print('='*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Word-by-word subtitle generator")
    parser.add_argument('--transcription', '-t', help='Transcription file (.txt)')
    parser.add_argument('--video', '-v', help='Input video file')
    parser.add_argument('-o', '--output', help='Output video file')
    parser.add_argument('--font', help='Path to font file')
    parser.add_argument('--font-name', default='Lato-Bold', help='Font name')
    parser.add_argument('--font-size', type=int, default=130, help='Font size')
    parser.add_argument('--fade', type=float, default=0.4, help='Fade duration')
    parser.add_argument('--api-key', help='Gemini API key')
    
    args = parser.parse_args()
    
    try:
        workflow = WordByWordSubtitleWorkflow(api_key=args.api_key, font_path=args.font)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        workflow.process(
            transcription_path=args.transcription,
            video_path=args.video,
            output_video_path=args.output,
            font_name=args.font_name,
            font_size=args.font_size,
            fade_duration=args.fade
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
