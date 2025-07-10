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
from config import GALLERY_SECRET_KEY, GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH


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
    """Push images and metadata to the gallery directory in current repository."""
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
        
        # Create directory path
        gallery_path = f"gallery/{generation_id}"
        
        # Prepare metadata
        metadata = {
            "id": generation_id,
            "timestamp": timestamp,
            "text": text,
            "sentiment_scores": sentiment_scores,
            "images": []
        }
        
        # Upload images
        for noise_type, image_bytes in images:
            image_filename = f"{noise_type}.png"
            image_path = f"{gallery_path}/{image_filename}"
            
            # Create or update file in repo
            try:
                repo.create_file(
                    path=image_path,
                    message=f"Add {noise_type} variation for '{text[:50]}...'",
                    content=image_bytes,
                    branch=GITHUB_BRANCH
                )
                metadata["images"].append({
                    "type": noise_type,
                    "filename": image_filename
                })
            except GithubException as e:
                if e.status == 422:  # File already exists
                    contents = repo.get_contents(image_path, ref=GITHUB_BRANCH)
                    # Handle single file response
                    if isinstance(contents, list):
                        contents = contents[0]
                    repo.update_file(
                        path=image_path,
                        message=f"Update {noise_type} variation",
                        content=image_bytes,
                        sha=contents.sha,
                        branch=GITHUB_BRANCH
                    )
                else:
                    raise
        
        # Upload metadata
        metadata_path = f"{gallery_path}/metadata.json"
        metadata_content = json.dumps(metadata, indent=2)
        
        try:
            repo.create_file(
                path=metadata_path,
                message=f"Add metadata for '{text[:50]}...'",
                content=metadata_content.encode(),
                branch=GITHUB_BRANCH
            )
        except GithubException as e:
            if e.status == 422:  # File already exists
                contents = repo.get_contents(metadata_path, ref=GITHUB_BRANCH)
                # Handle single file response
                if isinstance(contents, list):
                    contents = contents[0]
                repo.update_file(
                    path=metadata_path,
                    message=f"Update metadata",
                    content=metadata_content.encode(),
                    sha=contents.sha,
                    branch=GITHUB_BRANCH
                )
        
        print(f"Successfully pushed to GitHub: {gallery_path}")
        
    except ImportError:
        print("PyGithub not installed. Run: pip install PyGithub")
    except Exception as e:
        print(f"Error pushing to GitHub: {e}")
        raise


def fetch_gallery_items(limit: int = 10, offset: int = 0) -> List[GalleryItem]:
    """Fetch gallery items from GitHub repository."""
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
        
        # Get gallery directory contents
        try:
            contents = repo.get_contents("gallery", ref=GITHUB_BRANCH)
            # When getting a directory, it returns a list
            if not isinstance(contents, list):
                contents = [contents]
        except:
            # Gallery directory might not exist yet
            return []
        
        # Filter directories and sort by name (newest first)
        directories = [item for item in contents if item.type == "dir"]
        directories.sort(key=lambda x: x.name, reverse=True)
        
        # Apply pagination
        directories = directories[offset:offset + limit]
        
        # Load metadata for each directory
        items = []
        for dir_item in directories:
            try:
                # Fetch metadata.json
                metadata_file = repo.get_contents(f"{dir_item.path}/metadata.json", ref=GITHUB_BRANCH)
                # When getting a file, it returns a single ContentFile
                if isinstance(metadata_file, list):
                    metadata_file = metadata_file[0]
                metadata_content = base64.b64decode(metadata_file.content)
                metadata = json.loads(metadata_content)
                
                # Create GalleryItem
                item = GalleryItem(
                    id=metadata.get("id", dir_item.name),
                    timestamp=metadata.get("timestamp", ""),
                    text=metadata.get("text", ""),
                    sentiment_scores=metadata.get("sentiment_scores", {}),
                    images=metadata.get("images", [])
                )
                items.append(item)
            except Exception as e:
                print(f"Error loading metadata for {dir_item.name}: {e}")
                continue
        
        return items
        
    except Exception as e:
        print(f"Error fetching gallery items: {e}")
        return []


def fetch_gallery_image(generation_id: str, filename: str) -> Optional[str]:
    """Fetch a specific image from the gallery."""
    try:
        from github import Github
        
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
        
        # Fetch the image
        image_path = f"gallery/{generation_id}/{filename}"
        image_file = repo.get_contents(image_path, ref=GITHUB_BRANCH)
        # When getting a file, it returns a single ContentFile
        if isinstance(image_file, list):
            image_file = image_file[0]
        return image_file.content  # Already base64 encoded
        
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 