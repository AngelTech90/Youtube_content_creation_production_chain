#!/usr/bin/env python3
"""
YouTube Multi-Directory Video Uploader
=======================================
Automatically uploads ALL video packages from subdirectories.
Marks uploaded directories with "_uploaded" suffix to skip them on next run.
"""

import os
import json
import time
import random
import http.client
import httplib2
from pathlib import Path
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

# File paths for OAuth credentials and tokens
CLIENT_SECRETS_FILE = "credentials.json"
TOKEN_FILE = "youtube_token.json"

# Retry configuration
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


def authenticate_youtube():
    """Authenticate with YouTube Data API using OAuth 2.0"""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, [YOUTUBE_UPLOAD_SCOPE])
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"{CLIENT_SECRETS_FILE} not found. Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, [YOUTUBE_UPLOAD_SCOPE]
            )
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)
    return youtube


def read_text_file(file_path):
    """Read and return the contents of a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Warning: {file_path} not found.")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def parse_tags(tags_text):
    """Parse tags from text"""
    if not tags_text:
        return []
    
    if ',' in tags_text:
        tags = [tag.strip() for tag in tags_text.split(',')]
    else:
        tags = [tag.strip() for tag in tags_text.split()]
    
    cleaned_tags = []
    for tag in tags:
        tag = tag.strip()
        if tag:
            if tag.startswith('#'):
                tag = tag[1:]
            if tag:
                cleaned_tags.append(tag)
    
    return cleaned_tags


def resumable_upload(request):
    """Execute video upload with exponential backoff retry strategy"""
    response = None
    error = None
    retry = 0
    
    while response is None:
        try:
            print("Uploading video...")
            status, response = request.next_chunk()
            
            if response is not None:
                if 'id' in response:
                    print(f"Video uploaded successfully! Video ID: {response['id']}")
                    return response
                else:
                    raise Exception(f"Unexpected response: {response}")
            
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
        
        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                raise Exception("Maximum number of retries exceeded.")
            
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print(f"Retrying in {sleep_seconds:.2f} seconds...")
            time.sleep(sleep_seconds)


def upload_video(youtube, video_path, title, description, tags, category_id="22", privacy_status="private"):
    """Upload a video to YouTube with specified metadata"""
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        body = {
            'snippet': {
                'title': title[:100],
                'description': description[:5000],
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
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


def upload_thumbnail(youtube, video_id, thumbnail_path):
    """Upload and set a custom thumbnail for a YouTube video"""
    try:
        if not os.path.exists(thumbnail_path):
            print(f"Thumbnail file not found: {thumbnail_path}")
            return False
        
        file_size = os.path.getsize(thumbnail_path)
        if file_size > 2 * 1024 * 1024:
            print(f"Thumbnail file too large ({file_size / 1024 / 1024:.2f}MB). Maximum is 2MB.")
            return False
        
        print(f"Uploading thumbnail for video ID: {video_id}...")
        
        media = MediaFileUpload(thumbnail_path, mimetype='image/png', resumable=True)
        
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        )
        
        response = request.execute()
        print("Thumbnail uploaded successfully!")
        return True
        
    except HttpError as e:
        if e.resp.status == 403:
            print("\nError 403: Unable to upload thumbnail.")
            print("Your YouTube channel must be verified to upload custom thumbnails.")
            print("Verify your channel at: https://www.youtube.com/verify")
        else:
            print(f"An HTTP error occurred: {e.resp.status}\n{e.content}")
        return False
    except Exception as e:
        print(f"An error occurred uploading thumbnail: {e}")
        return False


def find_video_packages(base_folder):
    """
    Find all video package directories that haven't been uploaded yet.
    Skips directories with '_uploaded' suffix.
    Returns list of (directory_path, directory_name) tuples sorted alphabetically.
    """
    base_path = Path(base_folder)
    
    if not base_path.exists():
        print(f"Error: Base folder not found: {base_folder}")
        return []
    
    packages = []
    
    # Find all subdirectories
    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            # Skip if already uploaded
            if '_uploaded' in item.name:
                print(f"⏭  Skipping (already uploaded): {item.name}")
                continue
            
            # Check if it's a valid video package (has video file)
            video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv']
            has_video = False
            for ext in video_extensions:
                if list(item.glob(f'*{ext}')):
                    has_video = True
                    break
            
            if has_video:
                packages.append((item, item.name))
            else:
                print(f"⚠  Skipping (no video file): {item.name}")
    
    return packages


def mark_as_uploaded(directory_path):
    """Rename directory to add '_uploaded' suffix"""
    try:
        new_name = directory_path.name + "_uploaded"
        new_path = directory_path.parent / new_name
        directory_path.rename(new_path)
        print(f"✓ Marked as uploaded: {new_name}")
        return True
    except Exception as e:
        print(f"⚠ Failed to mark as uploaded: {e}")
        return False


def upload_video_package(video_folder_path, privacy_status="private", category_id="22"):
    """Upload a complete video package from a directory"""
    folder_path = Path(video_folder_path)
    
    print(f"\n{'='*60}")
    print(f"Processing video package: {folder_path.name}")
    print(f"{'='*60}\n")
    
    # Find video file
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv']
    video_file = None
    for ext in video_extensions:
        candidates = list(folder_path.glob(f'*{ext}'))
        if candidates:
            video_file = candidates[0]
            break
    
    if not video_file:
        print(f"Error: No video file found in {folder_path.name}")
        return None
    
    print(f"✓ Found video: {video_file.name}")
    
    # Read metadata files
    title = read_text_file(folder_path / "title.txt")
    description = read_text_file(folder_path / "description.txt")
    tags_text = read_text_file(folder_path / "tags.txt")
    
    if not title:
        title = video_file.stem
        print(f"⚠ No title.txt found, using filename: {title}")
    else:
        print(f"✓ Title: {title}")
    
    if not description:
        description = ""
        print("⚠ No description.txt found, using empty description")
    else:
        print(f"✓ Description loaded ({len(description)} characters)")
    
    tags = parse_tags(tags_text)
    if tags:
        print(f"✓ Tags: {', '.join(tags)}")
    else:
        print("⚠ No tags.txt found or no valid tags")
    
    # Find thumbnail
    thumbnail_extensions = ['.png', '.jpg', '.jpeg']
    thumbnail_file = None
    for ext in thumbnail_extensions:
        candidates = list(folder_path.glob(f'*{ext}'))
        if candidates:
            thumbnail_file = candidates[0]
            break
    
    if thumbnail_file:
        print(f"✓ Found thumbnail: {thumbnail_file.name}")
    else:
        print("⚠ No thumbnail found (optional)")
    
    # Authenticate
    print("\nAuthenticating with YouTube...")
    youtube = authenticate_youtube()
    print("✓ Authentication successful!")
    
    # Upload video
    print(f"\nUploading video (privacy: {privacy_status})...")
    video_id = upload_video(
        youtube,
        str(video_file),
        title,
        description,
        tags,
        category_id,
        privacy_status
    )
    
    if not video_id:
        print("❌ Video upload failed!")
        return None
    
    print(f"✓ Video uploaded! ID: {video_id}")
    print(f"   Watch at: https://www.youtube.com/watch?v={video_id}")
    
    # Upload thumbnail if available
    if thumbnail_file:
        print("\nUploading thumbnail...")
        success = upload_thumbnail(youtube, video_id, str(thumbnail_file))
        if success:
            print("✓ Thumbnail uploaded!")
        else:
            print("⚠ Thumbnail upload failed (video still uploaded successfully)")
    
    print(f"\n{'='*60}")
    print("Upload complete!")
    print(f"{'='*60}\n")
    
    return video_id


def main():
    """Main function - Process all video packages in subdirectories"""
    print("YouTube Multi-Directory Video Uploader")
    print("=" * 60)
    
    # CONFIGURATION
    BASE_FOLDER = "../../Upload_stage/videos_packages/"
    PRIVACY_STATUS = "private"
    CATEGORY_ID = "22"  # People & Blogs
    
    print(f"\nBase folder: {BASE_FOLDER}")
    print(f"Privacy: {PRIVACY_STATUS}")
    print(f"Category: {CATEGORY_ID}\n")
    print("=" * 60)
    
    # Find all video packages
    print("\n🔍 Scanning for video packages...\n")
    packages = find_video_packages(BASE_FOLDER)
    
    if not packages:
        print("\n❌ No video packages found to upload.")
        print("Place video packages in subdirectories of:")
        print(f"   {BASE_FOLDER}")
        return
    
    print(f"\n✅ Found {len(packages)} video package(s) to upload\n")
    print("=" * 60)
    
    # Upload each package
    uploaded_count = 0
    failed_count = 0
    
    for i, (package_path, package_name) in enumerate(packages, 1):
        print(f"\n📦 PACKAGE {i}/{len(packages)}: {package_name}")
        print("=" * 60)
        
        video_id = upload_video_package(
            package_path,
            privacy_status=PRIVACY_STATUS,
            category_id=CATEGORY_ID
        )
        
        if video_id:
            uploaded_count += 1
            # Mark directory as uploaded
            mark_as_uploaded(package_path)
            print(f"\n✅ Package {i}/{len(packages)} uploaded successfully!")
        else:
            failed_count += 1
            print(f"\n❌ Package {i}/{len(packages)} upload failed!")
        
        # Small delay between uploads
        if i < len(packages):
            print("\n⏳ Waiting 5 seconds before next upload...")
            time.sleep(5)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    print(f"Total packages found: {len(packages)}")
    print(f"Successfully uploaded: {uploaded_count}")
    print(f"Failed: {failed_count}")
    print("=" * 60)
    
    if uploaded_count > 0:
        print("\n✅ SUCCESS! Videos have been uploaded to YouTube.")
        if PRIVACY_STATUS == "private":
            print("\n💡 TIP: Videos are set to PRIVATE.")
            print("   Change privacy in YouTube Studio if needed.")


if __name__ == "__main__":
    main()
