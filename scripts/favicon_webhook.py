#!/usr/bin/env python3
"""
GitHub webhook handler for updating website favicon with Cue gallery images.

This script can be deployed as a serverless function or run as a simple Flask app.
It listens for GitHub push events and updates the favicon with a random image
from the latest Cue generation.
"""

import json
import random
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import base64
import os

# Flask example (can be adapted to other frameworks)
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
CUE_API_URL = os.getenv("CUE_API_URL", "http://localhost:8001")
FAVICON_OUTPUT_PATH = os.getenv("FAVICON_OUTPUT_PATH", "./static/favicon.png")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Optional: verify webhook signatures


def get_latest_from_api() -> Optional[Dict[str, Any]]:
    """Fetch the latest generation from Cue API."""
    try:
        response = requests.get(f"{CUE_API_URL}/gallery/latest")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch latest generation: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching from API: {e}")
        return None


def update_favicon(image_data_url: str, output_path: str) -> bool:
    """Save image data as favicon."""
    try:
        # Extract base64 data from data URL
        if image_data_url.startswith("data:image/png;base64,"):
            base64_data = image_data_url.split(",")[1]
            image_data = base64.b64decode(base64_data)
        else:
            print("Invalid image data URL format")
            return False
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write image data
        with open(output_path, "wb") as f:
            f.write(image_data)
        
        print(f"Favicon updated: {output_path}")
        return True
    except Exception as e:
        print(f"Failed to update favicon: {e}")
        return False


@app.route("/webhook", methods=["POST"])
def github_webhook():
    """Handle GitHub webhook push events."""
    # Verify webhook signature if configured (optional but recommended)
    # ... signature verification code here ...
    
    # Parse payload
    payload = request.json
    
    # Check if this is a push event
    if request.headers.get("X-GitHub-Event") != "push":
        return jsonify({"status": "ignored", "reason": "not a push event"}), 200
    
    # Check if files were added/modified in gallery/
    commits = payload.get("commits", [])
    gallery_updated = False
    
    for commit in commits:
        added_files = commit.get("added", [])
        modified_files = commit.get("modified", [])
        
        for file_path in added_files + modified_files:
            if file_path.startswith("gallery/"):
                gallery_updated = True
                break
        
        if gallery_updated:
            break
    
    if not gallery_updated:
        return jsonify({"status": "ignored", "reason": "no gallery updates"}), 200
    
    # Fetch latest generation from API
    latest_data = get_latest_from_api()
    if not latest_data:
        return jsonify({"status": "error", "reason": "failed to fetch latest generation"}), 500
    
    # Check if we have image data
    if "image_data_url" not in latest_data:
        return jsonify({"status": "error", "reason": "no image data in response"}), 500
    
    # Update favicon
    if update_favicon(latest_data["image_data_url"], FAVICON_OUTPUT_PATH):
        return jsonify({
            "status": "success",
            "generation_id": latest_data.get("item", {}).get("id", "unknown"),
            "text_preview": latest_data.get("item", {}).get("text", "")[:50] + "..."
        }), 200
    else:
        return jsonify({"status": "error", "reason": "failed to update favicon"}), 500


# Standalone script usage
def main():
    """Run as standalone script to manually update favicon."""
    print("Fetching latest generation from Cue API...")
    latest_data = get_latest_from_api()
    
    if not latest_data:
        print("Failed to fetch latest generation")
        return
    
    item = latest_data.get("item", {})
    print(f"Latest generation: {item.get('id', 'unknown')}")
    print(f"Text: {item.get('text', '')[:50]}...")
    
    if "image_data_url" in latest_data:
        if update_favicon(latest_data["image_data_url"], FAVICON_OUTPUT_PATH):
            print("Favicon updated successfully!")
        else:
            print("Failed to update favicon")
    else:
        print("No image data available")


if __name__ == "__main__":
    # Check if running as Flask app or standalone
    if os.getenv("FLASK_ENV"):
        app.run(host="0.0.0.0", port=5000)
    else:
        main() 