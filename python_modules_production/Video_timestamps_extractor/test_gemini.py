#!/usr/bin/env python3
"""
Video Transcription and Timestamp Analysis Script
Extracts transcription from audio using AssemblyAI API and analyzes it with Gemini AI
to identify optimal timestamps for complementary video clips.
"""
import re
import os
import sys
import pickle
import json
import time
import requests
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip

#We get any required mp4 in directory
def get_mp4_paths(path):
    mp4_paths = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if re.match(r'.*\.mp4', name):
                mp4_paths.append(os.path.join(root, name))
    return str(mp4_paths[0])

#We get any required .txt file in directory
def get_txt_paths(path):                
    txt_paths = [] 
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if re.match(r'.*\.txt', name):              
                txt_paths.append(os.path.join(root, name))  
    return str(txt_paths[0]) 

def get_video_duration(video_path: str = None) -> str:
    """Getting video duration for gemini AI prompt, formatted as MM:SS"""
    # If video_path is a list or None, get first path from get_mp4_paths
    if not video_path or isinstance(video_path, list):
        video_path = get_mp4_paths('../../Pre_production_content/videos')
        if isinstance(video_path, list):
            video_path = video_path[0] if video_path else None

    try:
        if video_path and Path(video_path).exists():
            clip = VideoFileClip(video_path)
            duration_seconds = int(round(clip.duration))
            clip.close()
            
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        else:
            print(f"Warning: Video path does not exist: {video_path}")
            return "01:00"  # fallback 60 seconds formatted
    except Exception as e:
        print(f"Warning: Could not get video duration: {e}")
        return "01:00"

class VideoTimestampAnalyzer:
    
    # Default paths - modify these to your preferences
    DEFAULT_INPUT_DIR = Path("../../Pre_production_content/audios")
    DEFAULT_VIDEO_INPUT_DIR = Path("../../Pre_production_content/videos")
    DEFAULT_TRANSCRIPTION_DIR = Path("../../in_production_content/transcriptions")
    DEFAULT_DATASET_DIR = Path("../../Core_data_workflow/data_sets")
    
    def __init__(self, gemini_api_key, assemblyai_api_key, audio_file: str = None):
        """
        Initialize the analyzer with Gemini and AssemblyAI API keys.
        
        Args:
            gemini_api_key (str): Google Gemini API key
            assemblyai_api_key (str): AssemblyAI API key
            audio_file (str): Path to local audio file (.mp3) - uses default if not specified
        """
        # Create default directories
        self.DEFAULT_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_TRANSCRIPTION_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_DATASET_DIR.mkdir(parents=True, exist_ok=True)
        
        self.gemini_api_key = gemini_api_key
        self.assemblyai_api_key = assemblyai_api_key
        
        # Set audio file - use provided or find first in default directory
        if audio_file:
            self.audio_file = Path(audio_file)
        else:
            # Find first audio file in default directory
            audio_files = list(self.DEFAULT_INPUT_DIR.glob('*.mp3')) + \
                         list(self.DEFAULT_INPUT_DIR.glob('*.wav')) + \
                         list(self.DEFAULT_INPUT_DIR.glob('*.m4a'))
            
            if audio_files:
                self.audio_file = audio_files[0]
                print(f"Using audio file: {self.audio_file.name}")
            else:
                raise FileNotFoundError(
                    f"No audio files found in {self.DEFAULT_INPUT_DIR}"
                )
        
        self.transcription_dir = self.DEFAULT_TRANSCRIPTION_DIR
        self.dataset_dir = self.DEFAULT_DATASET_DIR
        
        # Configure Gemini API
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # AssemblyAI endpoints
        self.assemblyai_base_url = "https://api.assemblyai.com/v2"
        
        # Generate output filenames based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
          
        self.transcription_file = get_txt_paths(f'{self.transcription_dir}')
        self.pkl_file = self.dataset_dir / f"transcription_{timestamp}_timestamps.pkl"
    
    def _milliseconds_to_timestamp(self, milliseconds):
        """Convert milliseconds to HH:MM:SS format."""
        seconds = milliseconds // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def analyze_with_gemini(self):
        """
        Send transcription to Gemini AI for analysis and extract timestamp dictionary.
        """
        print(f"\n[2/3] Analyzing transcription with Gemini AI...")
        
        # Read transcription
        with open(self.transcription_file, 'r', encoding='utf-8') as f:
            transcription = f.read()
        
        print(transcription)
        print(get_video_duration())

        # Prepare the prompt
        prompt = f"""Analyze this video transcription and find up to 11 segments where a complementary
clip would add context or visual enhancement.

For each segment, return the start and end timestamps (MM:SS) as tuples
in a single Python dictionary, using the following strict format:

{{
    "complementary_video_stamps_1": ("00:45", "00:55"),
    "complementary_video_stamps_2": ("01:22", "01:30")
}}

Rules:
- Return ONLY the dictionary. No code blocks, no explanations, no markdown.
- Ensure valid Python dictionary syntax.
- Do not return empty dicts.
- Make sure timestamps are inside the video duration ({get_video_duration}).

Video transcription:
{transcription}
"""
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            print("✓ Received response from Gemini AI")
            
            # Extract and parse the dictionary
            timestamps_dict = self._extract_dictionary(response_text)
            
            if timestamps_dict:
                print(f"✓ Successfully parsed {len(timestamps_dict)} timestamp entries")
                return timestamps_dict
            else:
                print("✗ Failed to parse valid dictionary from response")
                print("Raw response:")
                print(response_text)
                return None
            
        except Exception as e:
            print(f"✗ Error during Gemini AI analysis: {e}")
            return None
    
    def _extract_dictionary(self, text):
        """
        Extract Python dictionary from AI response text.
        Handles various formatting issues.
        """
        # Remove markdown code blocks if present
        text = re.sub(r'```python\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        try:
            # Try to evaluate as Python literal
            result = eval(text)
            if isinstance(result, dict):
                return result
        except Exception as e:
            print(f"Direct eval failed: {e}")
        
        # Try to find dictionary pattern in text
        dict_pattern = r'\{[^}]+\}'
        matches = re.finditer(dict_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                potential_dict = eval(match.group())
                if isinstance(potential_dict, dict):
                    return potential_dict
            except:
                continue
        
        return None
    
    def save_to_pickle(self, data):
        """
        Save the timestamp dictionary to a pickle file.
        
        Args:
            data (dict): Timestamp dictionary to save
        """
        print(f"\n[3/3] Saving results to pickle file...")
        
        if data is None:
            print("✗ No data to save")
            return False
        
        try:
            with open(self.pkl_file, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"✓ Data saved successfully")
            print(f"  Saved to: {self.pkl_file}")
            
            # Also save as JSON for easy viewing
            json_file = self.pkl_file.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  JSON copy: {json_file}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error saving pickle file: {e}")
            return False
    
    def run_full_pipeline(self):
        """Execute the complete pipeline."""
        print("=" * 60)
        print("Video Timestamp Analyzer - AssemblyAI + Gemini AI")
        print("=" * 60)
        
        # Analyze with Gemini
        timestamps = self.analyze_with_gemini()
        
        if timestamps is None:
            print("\n✗ Pipeline failed at analysis stage")
            return False
        
        # Save results
        if not self.save_to_pickle(timestamps):
            return False
        
        print("\n" + "=" * 60)
        print("✓ Pipeline completed successfully!")
        print("=" * 60)
        print(f"\nOutput files:")
        print(f"  - Transcription: {self.transcription_file}")
        print(f"  - Timestamps:    {self.pkl_file}")
        print(f"  - JSON:          {self.pkl_file.with_suffix('.json')}")
        
        return True


def main():
    """Main entry point for the script."""
    print("\n" + "=" * 60)
    print("Video Timestamp Analyzer")
    print("=" * 60 + "\n")
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API keys from .env file
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
    
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        print("\nPlease create a .env file with:")
        print("GEMINI_API_KEY=your-api-key-here")
        print("\nGet your API key at: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    if not assemblyai_api_key:
        print("Error: ASSEMBLYAI_API_KEY not found in .env file")
        print("\nPlease create a .env file with:")
        print("ASSEMBLYAI_API_KEY=your-api-key-here")
        print("\nGet your API key at: https://www.assemblyai.com/app/api-keys")
        sys.exit(1)
    
    # Get audio file from command line or use default
    audio_file = None
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    
    # Run the analyzer
    try:
        analyzer = VideoTimestampAnalyzer(gemini_api_key, assemblyai_api_key, audio_file)
        success = analyzer.run_full_pipeline()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Usage: python extract_and_analyze_timestamps.py [AUDIO_FILE]")
        print(f"\nExample:")
        print(f"  python extract_and_analyze_timestamps.py")
        print(f"  python extract_and_analyze_timestamps.py audio.mp3")
        print(f"  python extract_and_analyze_timestamps.py /path/to/audio.mp3")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
