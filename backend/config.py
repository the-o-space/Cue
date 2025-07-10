"""Configuration for Cue generative art project."""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Gallery Secret Key for GitHub push
GALLERY_SECRET_KEY = os.getenv("GALLERY_SECRET_KEY")

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "username/cue-gallery")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# Claude Model Configuration
MODEL_NAME = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 1024
TEMPERATURE = 0.3

# Sentiment Analysis Dimensions
SENTIMENT_DIMENSIONS = [
    "positiveness",    # 0.0 (cold colors) to 1.0 (warm colors)
    "energy",          # 0.0 (smooth) to 1.0 (chaotic/turbulent)
    "complexity",      # 0.0 (simple noise) to 1.0 (complex patterns)
    "conflictness",    # 0.0 (uniform colors) to 1.0 (high color variance)
]

# Art Generation Parameters
DEFAULT_IMAGE_SIZE = (1920, 1080)

# Color Temperature Mapping (for positiveness)
COLOR_TEMPERATURES = {
    "cold": [
        (25, 25, 80),      # Deep blue
        (40, 20, 90),      # Purple-blue
        (60, 40, 100),     # Lighter purple
    ],
    "neutral": [
        (80, 80, 80),      # Gray
        (70, 90, 70),      # Muted green
        (90, 85, 75),      # Warm gray
    ],
    "warm": [
        (180, 60, 30),     # Deep orange
        (220, 90, 40),     # Bright orange
        (240, 120, 50),    # Yellow-orange
    ]
}

# Noise Algorithm Thresholds (for complexity)
NOISE_COMPLEXITY_RANGES = {
    "gradient": (0.0, 0.2),
    "perlin": (0.2, 0.4),
    "fbm": (0.4, 0.6),
    "worley": (0.6, 0.8),
    "reaction_diffusion": (0.8, 1.0)
}

# Prompt template for sentiment analysis
SENTIMENT_PROMPT_TEMPLATE = """Analyze the following text and provide scores (0.0 to 1.0) for each dimension:

Text: "{text}"

Dimensions to analyze:
- positiveness: Overall emotional valence from negative/cold (0.0) to positive/warm (1.0)
- energy: Dynamic intensity from calm/smooth (0.0) to energetic/chaotic (1.0)
- complexity: Conceptual and structural complexity from simple (0.0) to complex (1.0)
- conflictness: Presence of conflicting emotions from uniform (0.0) to highly conflicted (1.0)

Return ONLY a JSON object with the dimension names as keys and scores as values.
Example: {{"positiveness": 0.8, "energy": 0.6, "complexity": 0.4, "conflictness": 0.2}}

JSON:""" 