# GitHub Gallery Setup

This guide explains how to set up the GitHub gallery feature for Cue.

## Overview

Cue uses your current repository to store generated images in a `gallery/` directory. When you provide the secret key, images are automatically pushed to this repository.

## Prerequisites

1. GitHub Personal Access Token with `repo` scope
2. The secret key configured in your environment

## Configuration

1. Set up environment variables in your `.env` file:

```bash
# Gallery Secret Key (choose a strong secret)
GALLERY_SECRET_KEY=your-secret-key-here

# GitHub Configuration
GITHUB_TOKEN=your-github-personal-access-token
# GITHUB_REPO is optional - if not set, it will auto-detect from git remote
# GITHUB_REPO=username/Cue
GITHUB_BRANCH=main
```

## Usage

1. In the Cue frontend, press `Cmd+/` (or `Ctrl+/` on Windows/Linux) to reveal the secret key field
2. Enter your secret key
3. Generate art as usual - it will automatically be pushed to the `gallery/` directory in your repository

## Gallery Structure

Images are organized in the repository as follows:

```
gallery/
├── 2024-01-20T15-30-45-123456_abcd1234/
│   ├── metadata.json
│   ├── terrain.png
│   ├── value.png
│   ├── worley.png
│   └── gradient.png
├── 2024-01-20T16-45-30-789012_efgh5678/
│   ├── metadata.json
│   └── ...
```

Each generation creates a unique folder with:
- Timestamp-based ID
- All 4 noise variations as PNG files
- metadata.json containing:
  - Generation timestamp
  - Original text prompt
  - Sentiment scores
  - Image filenames

## API Endpoints

The Cue backend provides API endpoints to access the gallery:

- `GET /gallery` - List gallery items with pagination
  - Query params: `limit` (default: 10), `offset` (default: 0)
- `GET /gallery/latest` - Get the most recent generation with a random image

## Setting Up GitHub Webhook for Favicon

To automatically update your website's favicon with the latest Cue generation:

1. Deploy the webhook script (see `scripts/favicon_webhook.py` or `.js`)
2. Set the environment variable:
   ```
   CUE_API_URL=https://your-cue-instance.com
   ```
3. Set up a GitHub webhook in your repository:
   - Payload URL: Your webhook endpoint
   - Content type: application/json
   - Events: Push events
4. The webhook will fetch from `/gallery/latest` and update your favicon

## Direct API Usage

You can also directly fetch the latest image from your frontend:

```javascript
// Fetch latest gallery item
const response = await fetch('https://your-cue-api.com/gallery/latest');
const data = await response.json();

// Use the image
if (data.image_data_url) {
  // data.image_data_url is a base64 data URL
  document.getElementById('favicon').href = data.image_data_url;
}
```

## Security Notes

- Keep your `GALLERY_SECRET_KEY` secure and don't commit it to version control
- Use environment variables for all sensitive configuration
- The GitHub token needs `repo` scope
- Consider using webhook signature verification for production deployments 