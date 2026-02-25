#!/usr/bin/env python3
"""
CleanVoice Audio Enhancer (Automatic Version)
---------------------------------------------
Enhances local MP3 audio files using CleanVoice AI API.

Workflow:
1. Scans default input directory for .mp3 files
2. Uploads them to file.io (temporary public URLs)
3. Sends each file to CleanVoice for enhancement
4. Downloads enhanced files to output directory
5. Deletes temporary jobs from CleanVoice

No arguments needed — just run:
    python cleanvoiceai_audio_enhancer.py
"""
from dotenv import load_dotenv
import requests
import time
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
import json

class CleanVoiceEnhancer:
    """CleanVoice API client with local file upload via file.io"""

    DEFAULT_INPUT_DIR = Path("../../Pre_production_content/audios")
    DEFAULT_OUTPUT_DIR = Path("../../in_production_content/enhanced_audios")
    BASE_URL = "https://api.cleanvoice.ai/v2"
    FILEIO_URL = "https://file.io"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize enhancer and directories."""
        # Load environment variables
        load_dotenv()
        
        self.DEFAULT_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self.api_key = api_key or os.getenv("CLEANVOICE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CleanVoice API key required.\n"
                "Set CLEANVOICE_API_KEY environment variable.\n"
                "Get your key at: https://app.cleanvoice.ai/settings"
            )

        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        })

    def get_local_mp3s(self) -> List[Path]:
        """Find all MP3 files in input directory."""
        files = lsist(self.DEFAULT_INPUT_DIR.rglob("*.mp3"))
        if not files:
            print(f"No MP3 files found in {self.DEFAULT_INPUT_DIR}")
        return files

    def upload_to_fileio(self, file_path: Path) -> str:
        """Upload a local file to file.io and return a public URL."""
        print(f"  Uploading {file_path.name} to file.io...")
        
        try:
            # file.io requires multipart/form-data, not using session headers
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "audio/mpeg")}
                
                # Don't send Content-Type header, let requests set it with boundary
                response = requests.post(
                    self.FILEIO_URL,
                    files=files,
                    timeout=120
                )
            
            # Debug response
            print(f"  Response status: {response.status_code}")
            print(f"  Response headers: {dict(response.headers)}")
            print(f"  Response text: {response.text[:200]}")
            
            response.raise_for_status()
            
            # Try to parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise Exception(f"Invalid JSON response: {response.text[:500]}")
            
            # Check if upload was successful
            if not data.get("success"):
                raise Exception(f"file.io upload failed: {data}")
            
            file_url = data.get("link")
            if not file_url:
                raise Exception(f"No link in response: {data}")
            
            print(f"  ✓ Uploaded to {file_url}")
            return file_url
            
        except requests.exceptions.Timeout:
            raise Exception(f"Upload timed out for {file_path.name}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to upload {file_path.name} to file.io: {str(e)}")

    def upload_to_tmpfiles_org(self, file_path: Path) -> str:
        """Alternative: Upload to tmpfiles.org (more reliable)."""
        print(f"  Uploading {file_path.name} to tmpfiles.org...")
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "audio/mpeg")}
                response = requests.post(
                    "https://tmpfiles.org/api/v1/upload",
                    files=files,
                    timeout=120
                )
            
            response.raise_for_status()
            data = response.json()
            
            # tmpfiles.org returns: {"status": "success", "data": {"url": "..."}}
            if data.get("status") != "success":
                raise Exception(f"Upload failed: {data}")
            
            # Extract the direct download URL
            url = data.get("data", {}).get("url")
            if not url:
                raise Exception(f"No URL in response: {data}")
            
            # Convert to direct download URL
            # tmpfiles.org returns: https://tmpfiles.org/123/file.mp3
            # We need: https://tmpfiles.org/dl/123/file.mp3
            url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            
            print(f"  ✓ Uploaded to {url}")
            return url
            
        except Exception as e:
            raise Exception(f"Failed to upload {file_path.name} to tmpfiles.org: {str(e)}")

    def create_edit(self, file_url: str, config: Optional[Dict] = None) -> str:
        """Create CleanVoice enhancement job."""
        config = config or {
            "remove_noise": True,
            "normalize": True,
            "studio_sound": "nightly",
            "fillers": True,
            "mouth_sounds": True,
            "breath": "natural",
            "export_format": "mp3"
        }

        payload = {"input": {"files": [file_url], "config": config}}
        print("  Creating CleanVoice job...")

        try:
            response = self.session.post(f"{self.BASE_URL}/edits", json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            edit_id = data.get("id")
            if not edit_id:
                raise Exception(f"No edit ID in response: {data}")
            print(f"  ✓ Job created: {edit_id}")
            return edit_id
        except requests.exceptions.RequestException as e:
            raise Exception(f"Create job failed: {str(e)}")

    def check_status(self, edit_id: str) -> Dict:
        """Check CleanVoice job status."""
        try:
            response = self.session.get(f"{self.BASE_URL}/edits/{edit_id}", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Status check failed: {str(e)}")

    def wait_for_completion(self, edit_id: str, timeout: int = 1800) -> str:
        """Wait until job finishes and return download URL."""
        print("  Processing audio...", end="", flush=True)
        start = time.time()
        interval = 3

        while time.time() - start < timeout:
            status_data = self.check_status(edit_id)
            status = status_data.get("status")

            if status == "SUCCESS":
                print(" Done!")
                result = status_data.get("result", {})
                url = result.get("download_url")
                if not url:
                    raise Exception("No download URL found in result.")
                return url
            elif status == "FAILURE":
                raise Exception("CleanVoice job failed.")
            else:
                print(".", end="", flush=True)
                time.sleep(interval)
        raise TimeoutError(f"Job timed out after {timeout} seconds")

    def download_file(self, url: str, output_path: Path):
        """Download processed audio file."""
        print(f"  Downloading to {output_path.name}...")
        try:
            with requests.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"  ✓ Saved: {output_path}")
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

    def delete_edit(self, edit_id: str):
        """Delete job from CleanVoice servers."""
        try:
            self.session.delete(f"{self.BASE_URL}/edits/{edit_id}", timeout=30)
            print(f"  ✓ Deleted job {edit_id}")
        except requests.exceptions.RequestException:
            print(f"  ⚠ Could not delete job {edit_id}")

    def enhance_local_file(self, file_path: Path):
        """Enhance a single local file (upload → process → download)."""
        print("\n" + "=" * 60)
        print(f"Processing: {file_path.name}")
        print("=" * 60)

        try:
            # Try tmpfiles.org first (more reliable)
            try:
                file_url = self.upload_to_tmpfiles_org(file_path)
            except Exception as e:
                print(f"  ⚠ tmpfiles.org failed: {e}")
                print(f"  Trying file.io as fallback...")
                file_url = self.upload_to_fileio(file_path)

            # Create CleanVoice job
            edit_id = self.create_edit(file_url)

            # Wait for completion
            download_url = self.wait_for_completion(edit_id)

            # Download enhanced file
            output_path = self.DEFAULT_OUTPUT_DIR / f"enhanced_{file_path.name}"
            self.download_file(download_url, output_path)

            # Cleanup
            self.delete_edit(edit_id)

            print(f"✓ Enhanced successfully → {output_path}")
        except Exception as e:
            print(f"✗ Failed to enhance {file_path.name}: {str(e)}")

    def run(self):
        """Main runner: enhance all local MP3 files."""
        print(f"\n{'=' * 60}")
        print("CLEANVOICE AUDIO ENHANCER (AUTO MODE)")
        print('=' * 60)
        print(f"Input:  {self.DEFAULT_INPUT_DIR.resolve()}")
        print(f"Output: {self.DEFAULT_OUTPUT_DIR.resolve()}")
        print('=' * 60)

        files = self.get_local_mp3s()
        if not files:
            print("No .mp3 files found to process.")
            return

        for file_path in files:
            self.enhance_local_file(file_path)

        print("\nAll files processed.\n")


if __name__ == "__main__":
    try:
        enhancer = CleanVoiceEnhancer()
        enhancer.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
