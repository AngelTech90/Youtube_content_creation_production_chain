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
    """Getting video duration for gemini AI prompt"""
    video_path = get_mp4_paths('../../Pre_production_content/videos')
    try:
        if video_path and Path(video_path).exists():
            clip = VideoFileClip(video_path)
        else:
            clip = VideoFileClip(video_path)
        duration_seconds = str(clip.duration)
        clip.close()
        return duration_seconds
    except Exception as e:
        print(f"Warning: Could not get video duration: {e}")
        return "60"

print(get_mp4_paths('../../Pre_production_content/videos'))
print(get_video_duration())
