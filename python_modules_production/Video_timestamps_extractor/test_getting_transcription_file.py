#!/usr/bin/env python3
"""
Video Transcription and Timestamp Analysis Script
Extracts transcription from audio using AssemblyAI API and analyzes it with Gemini AI
to identify optimal timestamps for complementary video clips.
"""

import os
import sys
import pickle
import json
import re
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip

#We get any .pkl file in directory
def get_mp4_paths(path):
    mp4_paths = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if re.match(r'.*\.mp4', name):
                mp4_paths.append(os.path.join(root, name))
    return str(mp4_paths[0])

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

print(get_mp4_paths('../../Pre_production_content/videos'))
print(get_video_duration())
