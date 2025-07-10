# Cue

Transform text into abstract art through sentiment analysis.

## Overview

Cue is an experimental generative art project that analyzes the emotional content of text and creates unique abstract visualizations. Using Claude AI for sentiment analysis across multiple dimensions (positiveness, energy, complexity, conflictness), it generates organic, noise-based art that reflects the emotional essence of your words.

## Features

- **Sentiment Analysis**: Advanced text analysis using Claude AI across four emotional dimensions
- **Multiple Noise Algorithms**: Generates variations using terrain, value, Worley, and gradient noise
- **Minimal UI**: Clean, floating text input that disappears after submission
- **GitHub Gallery Integration**: Automatically push generated art to a GitHub repository (with secret key)
- **Webhook Support**: Update external website favicons with your latest creations

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Cue.git
cd Cue
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Install and run backend:
```bash
cd backend
uv sync
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

4. Install and run frontend:
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

5. Open http://localhost:5173 in your browser

## GitHub Gallery Feature

### Setup

1. Create a GitHub Personal Access Token with `repo` scope
2. Configure environment variables in `.env`:
   ```
   GALLERY_SECRET_KEY=your-secret-key
   GITHUB_TOKEN=your-github-token
   GITHUB_REPO=username/cue-gallery
   ```

### Usage

1. Press `Cmd+/` (Mac) or `Ctrl+/` (Windows/Linux) in the frontend
2. Enter your secret key
3. Generate art - it will automatically push to your GitHub repository

### Webhook Integration

Use the provided webhook scripts to automatically update your website's favicon with the latest Cue generation. See `scripts/README.md` for detailed instructions.

## Architecture

- **Backend**: FastAPI server with sentiment analysis and art generation
- **Frontend**: React + TypeScript with Tailwind CSS
- **Art Generation**: Custom noise algorithms creating organic, gradient-based patterns
- **Storage**: GitHub repository for persistent gallery storage

## Development

See individual component documentation:
- Backend development: `backend/README.md`
- Frontend development: `frontend/README.md`
- Gallery setup: `docs/GITHUB_GALLERY_SETUP.md`

## License

MIT
