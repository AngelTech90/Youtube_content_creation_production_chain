#!/usr/bin/env python3
"""
CleanVoice Audio Enhancer
Enhance MP3 audio files using CleanVoice AI API
Remove background noise, filler words, and improve audio quality
"""

import requests
import time
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict
import argparse
import json
from urllib.parse import quote
import re

#We get ant .mp3 file in directory
def get_mp3_paths(path):
    mp3_paths = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if re.match(r'.*\.mp3', name):
                mp3_paths.append(os.path.join(root, name))
    return mp3_paths

class CleanVoiceEnhancer:
    """CleanVoice API v2 client for audio enhancement"""
    
    DEFAULT_INPUT_DIR = Path(get_mp3_paths("../../Pre_production_content/audios"))
    DEFAULT_OUTPUT_DIR = Path("../../in_production_content/enhanced_audios")

    BASE_URL = "https://api.cleanvoice.ai/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CleanVoice enhancer
        
        Args:
            api_key: CleanVoice API key (or set CLEANVOICE_API_KEY environment variable)
        """

        self.DEFAULT_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self.api_key = api_key or os.getenv("CLEANVOICE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CleanVoice API key required.\n"
                "Set CLEANVOICE_API_KEY environment variable or pass api_key parameter.\n"
                "Get your API key at: https://app.cleanvoice.ai/settings\n"
                "Pricing: Pay-per-use, affordable rates"
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        })
    
    def create_edit(self, file_url: str, config: Optional[Dict] = None) -> str:
        """
        Create an edit job with CleanVoice API
        
        Args:
            file_url: Public URL to audio/video file
            config: Enhancement configuration (optional)
            
        Returns:
            Edit job ID
        """
        # Default config with recommended settings
        if config is None:
            config = {
                "remove_noise": True,
                "normalize": True,
                "studio_sound": "nightly",
                "fillers": True,
                "mouth_sounds": True,
                "breath": "natural",
                "export_format": "mp3"
            }
        
        payload = {
            "input": {
                "files": [file_url],
                "config": config
            }
        }
        
        print(f"  Creating edit job...")
        print(f"  Config: {json.dumps(config, indent=2)}")
        
        try:
            response = self.session.post(
                f"{self.BASE_URL}/edits",
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            edit_id = data.get('id')
            
            if not edit_id:
                raise Exception(f"No edit ID in response: {data}")
            
            print(f"  ✓ Job created: {edit_id}")
            return edit_id
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_data.get('message', error_msg))
            except:
                pass
            raise Exception(f"Failed to create edit: {error_msg}")
    
    def check_status(self, edit_id: str) -> Dict:
        """
        Check edit job status
        
        Args:
            edit_id: Edit job ID
            
        Returns:
            Status dictionary with full edit details
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/edits/{edit_id}",
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Status check failed: {str(e)}")
    
    def wait_for_completion(self, edit_id: str, timeout: int = 1800) -> str:
        """
        Wait for edit to complete
        
        Args:
            edit_id: Edit job ID
            timeout: Maximum wait time in seconds (default: 30 minutes)
            
        Returns:
            Download URL of edited audio
        """
        print("  Processing audio...", end='', flush=True)
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            try:
                status_data = self.check_status(edit_id)
                status = status_data.get('status')
                
                if status == 'SUCCESS':
                    print(" Done!")
                    
                    # Get statistics
                    result = status_data.get('result', {})
                    stats = result.get('statistics', {})
                    
                    if stats:
                        print(f"\n  Edit Statistics:")
                        for key, value in stats.items():
                            print(f"    {key}: {value}")
                    
                    download_url = result.get('download_url')
                    if not download_url:
                        raise Exception("No download URL in response")
                    
                    return download_url
                
                elif status == 'FAILURE':
                    raise Exception("Edit job failed")
                
                elif status in ['PENDING', 'STARTED', 'RETRY']:
                    print(".", end='', flush=True)
                    time.sleep(check_interval)
                    # Increase check interval gradually (max 10 seconds)
                    if check_interval < 10:
                        check_interval = min(check_interval + 0.5, 10)
                
                else:
                    raise Exception(f"Unknown status: {status}")
                    
            except Exception as e:
                if "Status check failed" in str(e):
                    # Retry on connection errors
                    time.sleep(check_interval)
                    continue
                raise
        
        raise TimeoutError(f"Edit timeout after {timeout} seconds")
    
    def download_file(self, url: str, output_path: str):
        """
        Download edited audio
        
        Args:
            url: Download URL
            output_path: Where to save file
        """
        print(f"  Downloading to: {output_path}")
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"    Download: {progress:.1f}%", end='\r')
            
            print()  # New line after progress
            print(f"  ✓ Saved: {output_path}")
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Download failed: {str(e)}")
    
    def delete_edit(self, edit_id: str):
        """
        Delete edit job and files from CleanVoice servers
        
        Args:
            edit_id: Edit job ID to delete
        """
        try:
            response = self.session.delete(
                f"{self.BASE_URL}/edits/{edit_id}",
                timeout=30
            )
            response.raise_for_status()
            print(f"  ✓ Deleted edit job: {edit_id}")
        except requests.exceptions.RequestException as e:
            print(f"  ⚠ Failed to delete edit: {str(e)}")
    
    def upload_to_public_url(self, file_path: str) -> str:
        """
        Note: CleanVoice API requires PUBLIC URLs
        This is a helper to remind users they need to upload files themselves
        
        For local files, you must:
        1. Upload to public storage (S3, cloud storage, etc.)
        2. Get public URL
        3. Pass URL to this script
        """
        raise NotImplementedError(
            "CleanVoice API requires publicly accessible URLs.\n"
            "Please upload your file to public storage and provide the URL.\n"
            "Supported: S3, Google Cloud Storage, Azure Blob Storage, etc."
        )
    
    def enhance_file(self, file_url: str, output_path: str, config: Optional[Dict] = None, delete_after: bool = True) -> bool:
        """
        Complete enhancement workflow for single file
        
        Args:
            file_url: Public URL to audio file
            output_path: Output audio file path
            config: Enhancement configuration
            delete_after: Delete from CleanVoice servers after download
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"Processing: {file_url}")
        print('='*60)
        
        edit_id = None
        try:
            # Step 1: Create edit job
            edit_id = self.create_edit(file_url, config)
            
            # Step 2: Wait for completion
            download_url = self.wait_for_completion(edit_id)
            
            # Step 3: Download result
            self.download_file(download_url, output_path)
            
            print(f"✓ Success: {output_path}\n")
            return True
            
        except Exception as e:
            print(f"\n✗ Failed: {str(e)}\n")
            return False
        
        finally:
            # Clean up: Delete from CleanVoice servers
            if delete_after and edit_id:
                self.delete_edit(edit_id)
    
    def enhance_batch(self, file_urls: List[str], output_dir: str, config: Optional[Dict] = None, delete_after: bool = True) -> Dict:
        """Enhance multiple audio files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING: {len(file_urls)} files")
        print(f"Output directory: {output_dir}")
        print('='*60)
        
        results = {'success': 0, 'failed': 0, 'files': []}
        
        for i, file_url in enumerate(file_urls, 1):
            # Extract filename from URL
            filename = file_url.split('/')[-1].split('?')[0]
            if not filename or '.' not in filename:
                filename = f"enhanced_{i}.mp3"
            else:
                base = filename.rsplit('.', 1)[0]
                filename = f"enhanced_{base}.mp3"
            
            output_path = output_dir / filename
            
            print(f"\n[{i}/{len(file_urls)}]")
            
            success = self.enhance_file(file_url, str(output_path), config, delete_after)
            
            results['files'].append({
                'url': file_url,
                'output': str(output_path) if success else None,
                'status': 'success' if success else 'failed'
            })
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
        
        # Summary
        print("\n" + "="*60)
        print("BATCH COMPLETE")
        print("="*60)
        print(f"Total: {len(file_urls)}")
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")
        print("="*60 + "\n")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Enhance audio files using CleanVoice AI API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file (URL)
  python cleanvoice_enhancer.py "https://example.com/audio.mp3" -o output.mp3
  
  # Multiple files
  python cleanvoice_enhancer.py "https://example.com/file1.mp3" "https://example.com/file2.mp3" -o enhanced/
  
  # With custom configuration
  python cleanvoice_enhancer.py "https://example.com/audio.mp3" -o output.mp3 \\
      --remove-noise --normalize --fillers --mouth-sounds
  
  # With API key
  python cleanvoice_enhancer.py "https://example.com/audio.mp3" -o output.mp3 --api-key YOUR_KEY

IMPORTANT:
  CleanVoice API requires PUBLIC URLS. Upload your files to:
  - AWS S3
  - Google Cloud Storage
  - Azure Blob Storage
  - Any publicly accessible URL
  
  Then pass the URL to this script.

Environment:
  CLEANVOICE_API_KEY    Your CleanVoice API key

Get your API key at: https://app.cleanvoice.ai/settings
        """
    )
    
    parser.add_argument(
        'input',
        nargs='+',
        help='Public URL(s) to audio/video file(s)'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output file or directory'
    )
    
    parser.add_argument(
        '--api-key',
        help='CleanVoice API key'
    )
    
    # Enhancement options
    parser.add_argument(
        '--remove-noise',
        action='store_true',
        default=True,
        help='Remove background noise (default: True)'
    )
    
    parser.add_argument(
        '--normalize',
        action='store_true',
        default=True,
        help='Normalize audio levels (default: True)'
    )
    
    parser.add_argument(
        '--fillers',
        action='store_true',
        help='Remove filler sounds (um, uh, like, etc.)'
    )
    
    parser.add_argument(
        '--mouth-sounds',
        action='store_true',
        help='Remove mouth sounds'
    )
    
    parser.add_argument(
        '--breath',
        choices=['natural', 'muted', 'legacy', 'false'],
        default='natural',
        help='Breath control: natural (reduce), muted (remove), legacy (old algorithm), false (keep)'
    )
    
    parser.add_argument(
        '--long-silences',
        action='store_true',
        help='Remove long silences'
    )
    
    parser.add_argument(
        '--stutters',
        action='store_true',
        help='Remove stutters'
    )
    
    parser.add_argument(
        '--studio-sound',
        choices=['false', 'nightly'],
        default='nightly',
        help='Apply studio sound processing (default: nightly)'
    )
    
    parser.add_argument(
        '--keep-delete',
        action='store_true',
        help='Keep files on CleanVoice servers (they delete after 7 days anyway)'
    )
    
    args = parser.parse_args()
    
    # Initialize enhancer
    try:
        enhancer = CleanVoiceEnhancer(api_key=args.api_key)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Build config
    config = {
        "remove_noise": args.remove_noise,
        "normalize": args.normalize,
        "fillers": args.fillers,
        "mouth_sounds": args.mouth_sounds,
        "breath": args.breath if args.breath != 'false' else False,
        "long_silences": args.long_silences,
        "stutters": args.stutters,
        "studio_sound": args.studio_sound,
        "export_format": "mp3"
    }
    
    # Process files
    if len(args.input) == 1:
        success = enhancer.enhance_file(
            args.input[0],
            args.output,
            config,
            delete_after=not args.keep_delete
        )
        sys.exit(0 if success else 1)
    else:
        results = enhancer.enhance_batch(
            args.input,
            args.output,
            config,
            delete_after=not args.keep_delete
        )
        sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
