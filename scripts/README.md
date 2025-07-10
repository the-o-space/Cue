# Cue Gallery Webhook Scripts

This directory contains webhook handlers for integrating Cue gallery images with external websites.

## Available Scripts

### Python Webhook (`favicon_webhook.py`)

A Flask-based webhook handler that:
- Listens for GitHub push events
- Fetches the latest generation from Cue API
- Updates website favicon with the random image selected by the API

**Usage:**

```bash
# Install dependencies
pip install flask requests

# Set environment variables
export CUE_API_URL=http://localhost:8001  # or your Cue API URL
export FAVICON_OUTPUT_PATH=./static/favicon.png

# Run as Flask app
export FLASK_ENV=development
python favicon_webhook.py

# Or run standalone to manually update favicon
python favicon_webhook.py
```

### JavaScript Webhook (`favicon_webhook.js`)

A serverless function for Vercel/Netlify that:
- Handles GitHub webhooks
- Fetches latest image from Cue API
- Returns base64-encoded image data
- Includes client-side favicon updater function

**Deployment on Vercel:**

1. Create `api/webhook.js` in your project
2. Copy the handler code
3. Set environment variables in Vercel dashboard:
   ```
   CUE_API_URL=https://your-cue-instance.com
   ```
4. Add webhook URL to GitHub repository settings

**Client-side usage:**

```javascript
// Import the helper functions
import { 
  updateFaviconFromDataUrl, 
  updateFaviconFromCueGallery 
} from './favicon_webhook.js';

// Method 1: Update directly from Cue API
await updateFaviconFromCueGallery('https://your-cue-api.com');

// Method 2: Use with webhook response
fetch('/api/webhook-endpoint')
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      updateFaviconFromDataUrl(data.imageDataUrl);
    }
  });
```

## How It Works

1. When new images are pushed to the `gallery/` directory in your Cue repository
2. GitHub sends a webhook to your endpoint
3. The webhook handler:
   - Verifies it's a push event with gallery changes
   - Calls Cue API `/gallery/latest` endpoint
   - Gets a random image from the latest generation
   - Updates the favicon (Python) or returns the data (JavaScript)

## Setting Up GitHub Webhooks

1. Go to your Cue repository settings
2. Navigate to Webhooks > Add webhook
3. Set:
   - Payload URL: Your webhook endpoint
   - Content type: `application/json`
   - Events: Select "Push events"
   - Active: ✓

## API Integration

Both scripts use the Cue API endpoints:
- `/gallery/latest` - Returns the latest generation with a randomly selected image

No GitHub token is required for the webhook handlers since they use the public API.

## Security Considerations

- Use HTTPS for webhook endpoints
- Consider implementing webhook signature verification
- Ensure your Cue API is accessible from your webhook handler
- For production, implement rate limiting and error handling 