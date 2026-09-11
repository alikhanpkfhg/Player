#!/usr/bin/env python3
"""
Script to extract zip file and upload contents to GitHub repository
"""

import os
import base64
import zipfile
import io
import requests
from pathlib import Path

# Configuration
REPO_OWNER = "alikhanpkfhg"
REPO_NAME = "Player"
ZIP_FILE_NAME = "flutter-m3u-iptv-player-&-ios-ipa-builder.zip"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Set this as an environment variable
BRANCH = "main"

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set")

# GitHub API base URL
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def get_file_sha(file_path):
    """Get the SHA of a file in the repository"""
    try:
        response = requests.get(
            f"{API_BASE}/contents/{file_path}",
            headers=HEADERS,
            params={"ref": BRANCH}
        )
        if response.status_code == 200:
            return response.json()["sha"]
    except Exception as e:
        print(f"Could not get SHA for {file_path}: {e}")
    return None


def download_zip_from_repo():
    """Download the zip file from the repository"""
    print(f"Downloading {ZIP_FILE_NAME}...")
    response = requests.get(
        f"{API_BASE}/contents/{ZIP_FILE_NAME}",
        headers=HEADERS,
        params={"ref": BRANCH}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to download zip file: {response.status_code}")
    
    download_url = response.json()["download_url"]
    zip_response = requests.get(download_url)
    
    if zip_response.status_code != 200:
        raise Exception(f"Failed to download from {download_url}")
    
    return io.BytesIO(zip_response.content)


def extract_and_upload():
    """Extract zip and upload files to repository"""
    try:
        # Download zip file
        zip_buffer = download_zip_from_repo()
        
        # Extract zip
        print("Extracting zip file...")
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"Found {len(file_list)} items in zip")
            
            for file_path in file_list:
                # Skip directories
                if file_path.endswith('/'):
                    print(f"Skipping directory: {file_path}")
                    continue
                
                # Read file content
                file_content = zip_ref.read(file_path)
                
                # Encode to base64
                encoded_content = base64.b64encode(file_content).decode()
                
                # Upload to GitHub
                upload_file_to_github(file_path, encoded_content)
        
        print("✓ Extraction and upload complete!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        raise


def upload_file_to_github(file_path, encoded_content):
    """Upload a single file to GitHub repository"""
    try:
        # Check if file already exists
        existing_sha = get_file_sha(file_path)
        
        payload = {
            "message": f"Extract: Add {file_path}",
            "content": encoded_content,
            "branch": BRANCH
        }
        
        if existing_sha:
            payload["sha"] = existing_sha
        
        response = requests.put(
            f"{API_BASE}/contents/{file_path}",
            json=payload,
            headers=HEADERS
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ Uploaded: {file_path}")
        else:
            print(f"✗ Failed to upload {file_path}: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error uploading {file_path}: {e}")


if __name__ == "__main__":
    extract_and_upload()
