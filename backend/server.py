"""Simple FastAPI backend for Cue art generation."""

import os
import base64
from io import BytesIO
import json
from datetime import datetime
import hashlib
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sentiment_analyzer import SentimentAnalyzer
from art_generator import ArtGenerator
from config import GALLERY_SECRET_KEY, GITHUB_TOKEN, GITHUB_REPO


class GenerateRequest(BaseModel):
    text: str
    secret_key: Optional[str] = None


class GenerateResponse(BaseModel):
    images: list[str]  # Changed from image_url to images list
    sentiment_scores: dict


class GalleryItem(BaseModel):
    id: str
    timestamp: str
    text: str
    sentiment_scores: dict
    images: List[Dict[str, str]]


class GalleryResponse(BaseModel):
    items: List[GalleryItem]
    total: int


app = FastAPI(title="Cue API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize generators
sentiment_analyzer = SentimentAnalyzer()
art_generator = ArtGenerator()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Cue API"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_art(request: GenerateRequest):
    """Generate art from text."""
    try:
        # Analyze sentiment
        sentiment_scores = sentiment_analyzer.analyze(request.text)
        
        # Generate all noise variations
        variations = art_generator.generate_all_noise_variations(sentiment_scores)
        
        # Convert images to base64
        image_urls = []
        image_data_list = []  # Store for GitHub push
        
        for noise_type, image in variations.items():
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode()
            image_url = f"data:image/png;base64,{image_base64}"
            image_urls.append(image_url)
            image_data_list.append((noise_type, image_bytes))
        
        # Check if we should push to GitHub
        if request.secret_key and request.secret_key == GALLERY_SECRET_KEY:
            try:
                push_to_github_gallery(
                    text=request.text,
                    sentiment_scores=sentiment_scores,
                    images=image_data_list
                )
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to push to GitHub: {e}")
        
        return GenerateResponse(
            images=image_urls,
            sentiment_scores=sentiment_scores
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gallery", response_model=GalleryResponse)
async def get_gallery(limit: int = 10, offset: int = 0):
    """Get gallery items from the repository."""
    try:
        items = fetch_gallery_items(limit=limit, offset=offset)
        return GalleryResponse(
            items=items,
            total=len(items)  # In a real implementation, this would be the total count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gallery/latest")
async def get_latest_gallery_item():
    """Get the most recent gallery item."""
    try:
        items = fetch_gallery_items(limit=1)
        if not items:
            raise HTTPException(status_code=404, detail="No gallery items found")
        
        # Get a random image from the latest item
        latest = items[0]
        if latest.images:
            import random
            selected_image = random.choice(latest.images)
            
            # Fetch the actual image data if needed
            image_data = fetch_gallery_image(latest.id, selected_image["filename"])
            if image_data:
                return {
                    "item": latest,
                    "selected_image": selected_image,
                    "image_data_url": f"data:image/png;base64,{image_data}"
                }
        
        return {"item": latest}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def push_to_github_gallery(text: str, sentiment_scores: dict, images: list):
    """Push images and metadata as a GitHub release."""
    try:
        from github import Github, GithubException
        
        if not GITHUB_TOKEN:
            print("GitHub token missing")
            return
        
        # Create GitHub client
        g = Github(GITHUB_TOKEN)
        
        # Determine repository - if GITHUB_REPO is not set, try to detect from git
        repo_name = GITHUB_REPO
        if not repo_name or repo_name == "username/cue-gallery":
            # Try to detect current repository
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                remote_url = result.stdout.strip()
                # Extract owner/repo from URL
                if "github.com" in remote_url:
                    if remote_url.endswith(".git"):
                        remote_url = remote_url[:-4]
                    parts = remote_url.split("github.com")[-1].strip("/").split("/")
                    if len(parts) >= 2:
                        repo_name = f"{parts[-2]}/{parts[-1]}"
            except:
                print("Could not detect repository from git remote")
                return
        
        if not repo_name:
            print("Could not determine repository")
            return
            
        repo = g.get_repo(repo_name)
        
        # Generate unique ID for this generation
        timestamp = datetime.now().isoformat()
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        generation_id = f"{timestamp.replace(':', '-').replace('.', '-')}_{text_hash}"
        
        # Create release tag
        tag_name = f"generation-{generation_id}"
        release_name = f"{text[:50]}{'...' if len(text) > 50 else ''}"
        
        # Create release body with sentiment scores
        release_body = f"""**Text Prompt:**
{text}

**Sentiment Analysis:**
- Positiveness: {sentiment_scores.get('positiveness', 0):.2f}
- Energy: {sentiment_scores.get('energy', 0):.2f}
- Complexity: {sentiment_scores.get('complexity', 0):.2f}
- Conflictness: {sentiment_scores.get('conflictness', 0):.2f}

**Generated:** {timestamp}
**ID:** {generation_id}
"""
        
        # Create the release
        try:
            release = repo.create_git_release(
                tag=tag_name,
                name=release_name,
                message=release_body,
                draft=False,
                prerelease=False
            )
            print(f"Created release: {tag_name}")
        except GithubException as e:
            if "already_exists" in str(e):
                print(f"Release {tag_name} already exists")
                return
            else:
                raise
        
        # Prepare metadata
        metadata = {
            "id": generation_id,
            "timestamp": timestamp,
            "text": text,
            "sentiment_scores": sentiment_scores,
            "images": [],
            "release_tag": tag_name
        }
        
        # Upload images as release assets
        import tempfile
        import os
        
        for noise_type, image_bytes in images:
            image_filename = f"{noise_type}.png"
            
            try:
                print(f"  → Uploading {image_filename} ({len(image_bytes)} bytes)")
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(image_bytes)
                    temp_path = temp_file.name
                
                asset = release.upload_asset(
                    path=temp_path,
                    name=image_filename
                )
                
                # Clean up temp file
                os.unlink(temp_path)
                
                metadata["images"].append({
                    "type": noise_type,
                    "filename": image_filename,
                    "download_url": asset.browser_download_url
                })
                print(f"  ✓ Uploaded {image_filename} successfully")
            except Exception as e:
                print(f"  ✗ Failed to upload {image_filename}: {e}")
                import traceback
                print(f"  Full traceback: {traceback.format_exc()}")
                # Clean up temp file if it exists
                try:
                    if 'temp_path' in locals():
                        os.unlink(temp_path)
                except:
                    pass
        
        # Upload metadata as release asset
        metadata_content = json.dumps(metadata, indent=2)
        try:
            print(f"  → Uploading metadata.json ({len(metadata_content)} chars)")
            
            # Create temporary file for metadata
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as temp_file:
                temp_file.write(metadata_content)
                temp_path = temp_file.name
            
            metadata_asset = release.upload_asset(
                path=temp_path,
                name="metadata.json"
            )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            print(f"  ✓ Uploaded metadata.json successfully")
        except Exception as e:
            print(f"  ✗ Failed to upload metadata: {e}")
            import traceback
            print(f"  Full traceback: {traceback.format_exc()}")
            # Clean up temp file if it exists
            try:
                if 'temp_path' in locals():
                    os.unlink(temp_path)
            except:
                pass
        
        print(f"Successfully created release: {release.html_url}")
        
    except ImportError:
        print("PyGithub not installed. Run: pip install PyGithub")
    except Exception as e:
        print(f"Error creating release: {e}")
        raise


def fetch_gallery_items(limit: int = 10, offset: int = 0) -> List[GalleryItem]:
    """Fetch gallery items from GitHub releases."""
    try:
        from github import Github
        
        if not GITHUB_TOKEN:
            return []
        
        g = Github(GITHUB_TOKEN)
        
        # Determine repository
        repo_name = GITHUB_REPO
        if not repo_name or repo_name == "username/cue-gallery":
            # Try to detect current repository
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                remote_url = result.stdout.strip()
                if "github.com" in remote_url:
                    if remote_url.endswith(".git"):
                        remote_url = remote_url[:-4]
                    parts = remote_url.split("github.com")[-1].strip("/").split("/")
                    if len(parts) >= 2:
                        repo_name = f"{parts[-2]}/{parts[-1]}"
            except:
                return []
        
        if not repo_name:
            return []
            
        repo = g.get_repo(repo_name)
        
        # Get releases (GitHub API returns them sorted by created_at desc)
        releases = repo.get_releases()
        
        # Filter only generation releases and apply pagination
        generation_releases = []
        count = 0
        for release in releases:
            if release.tag_name.startswith("generation-"):
                if count >= offset:
                    generation_releases.append(release)
                    if len(generation_releases) >= limit:
                        break
                count += 1
        
        # Load metadata for each release
        items = []
        for release in generation_releases:
            try:
                # Find metadata.json asset
                metadata_asset = None
                for asset in release.get_assets():
                    if asset.name == "metadata.json":
                        metadata_asset = asset
                        break
                
                if metadata_asset:
                    # Download and parse metadata
                    import requests
                    response = requests.get(metadata_asset.browser_download_url)
                    metadata = response.json()
                else:
                    # Fallback: parse from release info
                    metadata = {
                        "id": release.tag_name.replace("generation-", ""),
                        "timestamp": release.created_at.isoformat(),
                        "text": release.name,
                        "sentiment_scores": {},
                        "images": []
                    }
                    
                    # Add image info from assets
                    for asset in release.get_assets():
                        if asset.name.endswith('.png'):
                            noise_type = asset.name.replace('.png', '')
                            metadata["images"].append({
                                "type": noise_type,
                                "filename": asset.name,
                                "download_url": asset.browser_download_url
                            })
                
                # Create GalleryItem
                item = GalleryItem(
                    id=metadata.get("id", release.tag_name),
                    timestamp=metadata.get("timestamp", release.created_at.isoformat()),
                    text=metadata.get("text", release.name),
                    sentiment_scores=metadata.get("sentiment_scores", {}),
                    images=metadata.get("images", [])
                )
                items.append(item)
                
            except Exception as e:
                print(f"Error loading metadata for {release.tag_name}: {e}")
                continue
        
        return items
        
    except Exception as e:
        print(f"Error fetching gallery items: {e}")
        return []


def fetch_gallery_image(generation_id: str, filename: str) -> Optional[str]:
    """Fetch a specific image from GitHub releases."""
    try:
        from github import Github
        import requests
        
        if not GITHUB_TOKEN:
            return None
        
        g = Github(GITHUB_TOKEN)
        
        # Determine repository (same logic as above)
        repo_name = GITHUB_REPO
        if not repo_name or repo_name == "username/cue-gallery":
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                remote_url = result.stdout.strip()
                if "github.com" in remote_url:
                    if remote_url.endswith(".git"):
                        remote_url = remote_url[:-4]
                    parts = remote_url.split("github.com")[-1].strip("/").split("/")
                    if len(parts) >= 2:
                        repo_name = f"{parts[-2]}/{parts[-1]}"
            except:
                return None
        
        if not repo_name:
            return None
            
        repo = g.get_repo(repo_name)
        
        # Find the release
        tag_name = f"generation-{generation_id}"
        try:
            release = repo.get_release(tag_name)
        except:
            return None
        
        # Find the asset
        for asset in release.get_assets():
            if asset.name == filename:
                # Download the image and convert to base64
                response = requests.get(asset.browser_download_url)
                if response.status_code == 200:
                    return base64.b64encode(response.content).decode()
                
        return None
        
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 