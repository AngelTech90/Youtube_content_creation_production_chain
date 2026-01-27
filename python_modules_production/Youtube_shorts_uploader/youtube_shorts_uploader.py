#!/usr/bin/env python3
"""
YouTube Shorts Auto-Upload Script with Package Management
==========================================================
This script automatically uploads YouTube Shorts from packages and marks them as uploaded.

YouTube Shorts Requirements:
- Video must be vertical (9:16 aspect ratio preferred)
- Duration: Maximum 60 seconds
- Resolution: Minimum 720p, recommended 1080x1920
- Title must include "#Shorts" for proper categorization

Prerequisites:
1. Install required packages: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
2. Enable YouTube Data API v3 in Google Cloud Console
3. Create OAuth 2.0 credentials and download client_secrets.json
4. Place client_secrets.json in the same directory as this script
"""

import os
import json
import time
import random
import http.client
import httplib2
import sys
from pathlib import Path
from typing import Optional, List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# YouTube API Configuration
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Default paths
DEFAULT_SHORTS_PACKAGES = Path("../../Upload_stage/shorts_packages")

# File paths for OAuth credentials and tokens
CLIENT_SECRETS_FILE = "credentials.json"
TOKEN_FILE = "youtube_token.json"

# Retry configuration for handling network issues during upload
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
MAX_RETRIES = 10


def get_first_available_package_dir(base_path: Path) -> Optional[Path]:
    """Get first directory in shorts_packages that doesn't have '_uploaded' suffix"""
    if not base_path.exists():
        return None
    
    # Get all subdirectories, sorted alphabetically
    subdirs = sorted([d for d in base_path.iterdir() if d.is_dir()])
    
    for subdir in subdirs:
        if '_uploaded' not in subdir.name:
            return subdir
    
    return None


def mark_package_as_uploaded(package_dir: Path) -> Path:
    """Add '_uploaded' suffix to package directory name"""
    new_name = package_dir.name + "_uploaded"
    new_path = package_dir.parent / new_name
    package_dir.rename(new_path)
    return new_path


def authenticate_youtube():
    """
    Authenticate with YouTube Data API using OAuth 2.0.
    
    Returns:
        youtube: Authorized YouTube API service instance
    """
    creds = None
    
    # Check if token file exists (stores user's access and refresh tokens)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, [YOUTUBE_UPLOAD_SCOPE])
    
    # If credentials don't exist or are invalid, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired credentials
            creds.refresh(Request())
        else:
            # Run OAuth flow for new credentials
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"{CLIENT_SECRETS_FILE} not found. Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, [YOUTUBE_UPLOAD_SCOPE]
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    # Build and return the YouTube service
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)
    return youtube


def read_text_file(file_path):
    """
    Read and return the contents of a text file.
    
    Args:
        file_path: Path to the text file
    
    Returns:
        content: File content as string, or None if file doesn't exist
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Warning: {file_path} not found.")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def parse_hashtags(tags_text):
    """
    Parse hashtags from text. Ensures #Shorts is included and properly formatted.
    
    Args:
        tags_text: String containing hashtags
    
    Returns:
        list: List of hashtag strings (without # symbol for API)
    """
    if not tags_text:
        return ["Shorts"]  # Default to just Shorts tag
    
    # Try comma-separated first
    if ',' in tags_text:
        tags = [tag.strip() for tag in tags_text.split(',')]
    else:
        # Fall back to space-separated
        tags = [tag.strip() for tag in tags_text.split()]
    
    # Clean and process tags
    cleaned_tags = []
    has_shorts = False
    
    for tag in tags:
        tag = tag.strip()
        if tag:
            # Remove # if present (YouTube API doesn't need it in tags array)
            if tag.startswith('#'):
                tag = tag[1:]
            
            # Check if Shorts tag exists
            if tag.lower() == 'shorts':
                has_shorts = True
            
            if tag:
                cleaned_tags.append(tag)
    
    # Ensure Shorts tag is always present
    if not has_shorts:
        cleaned_tags.insert(0, "Shorts")
    
    return cleaned_tags


def ensure_shorts_title(title):
    """
    Ensure title includes #Shorts for proper categorization.
    
    Args:
        title: Original video title
    
    Returns:
        str: Title with #Shorts included
    """
    if not title:
        return "#Shorts"
    
    # Check if #Shorts or #shorts already exists
    if '#shorts' not in title.lower():
        # Add #Shorts at the end if not present
        if len(title) <= 90:  # Leave room for " #Shorts"
            return f"{title} #Shorts"
        else:
            # If title is too long, truncate and add #Shorts
            return f"{title[:90]} #Shorts"
    
    return title


def validate_shorts_requirements(video_path):
    """
    Check if video meets basic Shorts requirements (file existence).
    Note: Duration and aspect ratio validation require additional libraries.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        tuple: (is_valid, warning_message)
    """
    if not os.path.exists(video_path):
        return False, f"Video file not found: {video_path}"
    
    file_size = os.path.getsize(video_path)
    file_size_mb = file_size / (1024 * 1024)
    
    warnings = []
    
    # Check file size (Shorts are typically small)
    if file_size_mb > 100:
        warnings.append(f"⚠ Large file size ({file_size_mb:.1f}MB). Shorts are usually under 50MB.")
    
    # Note: Aspect ratio and duration validation would require video processing libraries
    warnings.append("ℹ️  Remember: Shorts should be vertical (9:16), max 60 seconds")
    
    return True, "\n".join(warnings) if warnings else None


def resumable_upload(request):
    """
    Execute video upload with exponential backoff retry strategy.
    
    Args:
        request: MediaFileUpload request object
    
    Returns:
        response: YouTube API response with video details
    """
    response = None
    error = None
    retry = 0
    
    while response is None:
        try:
            print("Uploading Short...")
            status, response = request.next_chunk()
            
            if response is not None:
                if 'id' in response:
                    print(f"Short uploaded successfully! Video ID: {response['id']}")
                    return response
                else:
                    raise Exception(f"Unexpected response: {response}")
            
            # Show upload progress
            if status:
                progress = int(status.progress() * 100)
                print(f"Upload progress: {progress}%")
                
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = f"A retriable error occurred: {e}"
        
        # Handle retry logic with exponential backoff
        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                raise Exception("Maximum number of retries exceeded.")
            
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print(f"Retrying in {sleep_seconds:.2f} seconds...")
            time.sleep(sleep_seconds)


def upload_short(youtube, video_path, title, description, hashtags, privacy_status="public"):
    """
    Upload a YouTube Short with optimized metadata.
    
    Args:
        youtube: Authorized YouTube API service instance
        video_path: Path to the vertical video file
        title: Video title (will automatically include #Shorts)
        description: Short description (keep concise for Shorts)
        hashtags: List of hashtags (Shorts will be added if missing)
        privacy_status: "public", "private", or "unlisted" (public recommended for Shorts)
    
    Returns:
        video_id: ID of the uploaded Short, or None if failed
    """
    try:
        # Validate video file
        is_valid, warning = validate_shorts_requirements(video_path)
        if not is_valid:
            raise FileNotFoundError(warning)
        
        if warning:
            print(warning)
        
        # Ensure title includes #Shorts
        optimized_title = ensure_shorts_title(title)
        
        # Prepare video metadata optimized for Shorts
        body = {
            'snippet': {
                'title': optimized_title[:100],  # YouTube limit: 100 characters
                'description': description[:5000],  # Keep it short for Shorts!
                'tags': hashtags,
                'categoryId': '24'  # Entertainment category works best for Shorts
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False,  # Set based on your content
                'madeForKids': False
            }
        }
        
        # Create media upload object
        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        # Execute the upload request
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        # Upload with retry logic
        response = resumable_upload(request)
        
        if response and 'id' in response:
            return response['id']
        return None
        
    except HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status}\n{e.content}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def upload_short_package(short_folder, privacy_status="public"):
    """
    Upload a complete YouTube Short package (video + metadata).
    
    Expected folder structure:
        short_folder/
            ├── short_01_*.mp4  (or any .mp4 file)
            ├── title.txt       (optional, uses filename if missing)
            ├── description.txt (optional)
            └── tags.txt        (optional, hashtags)
    
    Args:
        short_folder: Path to folder containing Short assets
        privacy_status: "public" (recommended), "private", or "unlisted"
    
    Returns:
        video_id: ID of uploaded Short, or None if failed
    """
    folder_path = Path(short_folder)
    
    if not folder_path.exists():
        print(f"Error: Folder not found: {short_folder}")
        return None
    
    print(f"\n{'='*60}")
    print(f"Processing YouTube Short: {folder_path.name}")
    print(f"{'='*60}\n")
    
    # Find video file
    video_extensions = ['.mp4', '.mov', '.webm', '.avi']
    video_file = None
    for ext in video_extensions:
        candidates = list(folder_path.glob(f'*{ext}'))
        if candidates:
            video_file = candidates[0]
            break
    
    if not video_file:
        print(f"Error: No video file found in {short_folder}")
        print(f"Supported formats: {', '.join(video_extensions)}")
        return None
    
    print(f"✓ Found video: {video_file.name}")
    
    # Read metadata files
    title = read_text_file(folder_path / "title.txt")
    description = read_text_file(folder_path / "description.txt")
    hashtags_text = read_text_file(folder_path / "tags.txt")
    
    # Use filename as fallback for title
    if not title:
        title = video_file.stem.replace('_', ' ')
        print(f"⚠ No title.txt found, using filename: {title}")
    else:
        print(f"✓ Title: {title}")
    
    # Shorts descriptions should be concise
    if not description:
        description = ""
        print("⚠ No description.txt found")
    else:
        if len(description) > 500:
            print(f"⚠ Description is long ({len(description)} chars). Consider shortening for Shorts.")
        print(f"✓ Description loaded ({len(description)} characters)")
    
    # Parse hashtags - ensure #Shorts is included
    hashtags = parse_hashtags(hashtags_text)
    print(f"✓ Hashtags: {', '.join(['#' + tag for tag in hashtags])}")
    
    # Note: Shorts don't support custom thumbnails
    print("ℹ️  Note: YouTube auto-generates thumbnails for Shorts")
    
    # Authenticate with YouTube
    print("\nAuthenticating with YouTube...")
    youtube = authenticate_youtube()
    print("✓ Authentication successful!")
    
    # Upload Short
    print(f"\nUploading Short (privacy: {privacy_status})...")
    print("💡 Tip: 'public' works best for Shorts discovery")
    
    video_id = upload_short(
        youtube,
        str(video_file),
        title,
        description,
        hashtags,
        privacy_status
    )
    
    if not video_id:
        print("❌ Short upload failed!")
        return None
    
    print(f"✓ Short uploaded! ID: {video_id}")
    print(f"   Watch at: https://www.youtube.com/shorts/{video_id}")
    print(f"   Regular URL: https://www.youtube.com/watch?v={video_id}")
    
    print(f"\n{'='*60}")
    print("Upload complete!")
    print(f"{'='*60}\n")
    
    print("📱 Pro Tips for Shorts Success:")
    print("   • Hook viewers in first 3 seconds")
    print("   • Use trending sounds and hashtags")
    print("   • Post consistently (daily if possible)")
    print("   • Engage with comments quickly")
    print("   • Check YouTube Shorts analytics")
    
    return video_id


def main():
    """
    Main function - Automatically finds and uploads first available shorts package.
    """
    print("\n" + "="*60)
    print("YOUTUBE SHORTS AUTO-UPLOADER")
    print("="*60 + "\n")
    
    # Configuration
    PRIVACY_STATUS = "public"  # "public", "private", or "unlisted"
    
    # Find first available shorts package
    print("Looking for shorts packages...")
    package_dir = get_first_available_package_dir(DEFAULT_SHORTS_PACKAGES)
    
    if not package_dir:
        print("\n⚠ No available shorts packages found in:")
        print(f"   {DEFAULT_SHORTS_PACKAGES}")
        print("\nAll packages may already be uploaded (have '_uploaded' suffix)")
        print("Script execution ended.")
        sys.exit(0)
    
    print(f"✓ Found package: {package_dir.name}\n")
    
    # Upload the package
    try:
        video_id = upload_short_package(package_dir, privacy_status=PRIVACY_STATUS)
        
        if video_id:
            print("\n✅ SUCCESS! Your Short has been uploaded.")
            print(f"Shorts URL: https://www.youtube.com/shorts/{video_id}")
            print(f"Regular URL: https://www.youtube.com/watch?v={video_id}")
            
            # Mark package as uploaded
            print("\nMarking package as uploaded...")
            new_path = mark_package_as_uploaded(package_dir)
            print(f"✓ Renamed to: {new_path.name}")
            
            print("\n🚀 Remember: Shorts take time to get picked up by the algorithm!")
            print("   Check back in a few hours to see performance.")
            
            print("\n" + "="*60)
            print("✓ COMPLETE")
            print("="*60 + "\n")
            
        else:
            print("\n❌ Upload failed. Please check the error messages above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
