"""Simple FastAPI backend for Cue art generation."""

import os
import base64
from io import BytesIO

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sentiment_analyzer import SentimentAnalyzer
from art_generator import ArtGenerator


class GenerateRequest(BaseModel):
    text: str


class GenerateResponse(BaseModel):
    image_url: str
    sentiment_scores: dict


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
        
        # Generate art
        image = art_generator.generate(sentiment_scores)
        
        # Convert image to base64
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Return data URL
        image_url = f"data:image/png;base64,{image_base64}"
        
        return GenerateResponse(
            image_url=image_url,
            sentiment_scores=sentiment_scores
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 