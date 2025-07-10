# Cue Gallery Examples

This directory contains example implementations showing how to integrate Cue gallery images into external websites.

## Available Examples

### update_favicon.html

A standalone HTML page that demonstrates:
- Fetching the latest gallery item from the Cue API
- Updating the browser favicon dynamically
- Checking gallery status
- Showing a preview of the selected image

**Usage:**
1. Make sure your Cue backend is running (`http://localhost:8001`)
2. Open `update_favicon.html` in a web browser
3. Click "Update Favicon" to fetch and apply the latest image
4. The favicon will change to a random variation from the latest generation

**Features:**
- Configurable API URL
- Error handling and status messages
- Image preview
- Complete integration code example

## Integration Patterns

### Basic Favicon Update

```javascript
async function updateFaviconFromCue(apiUrl) {
    const response = await fetch(`${apiUrl}/gallery/latest`);
    const data = await response.json();
    
    if (data.image_data_url) {
        const link = document.querySelector("link[rel*='icon']") || 
                    document.createElement('link');
        link.type = 'image/png';
        link.rel = 'icon';
        link.href = data.image_data_url;
        document.head.appendChild(link);
    }
}
```

### Periodic Updates

```javascript
// Update favicon every hour
setInterval(() => {
    updateFaviconFromCue('https://your-cue-api.com');
}, 60 * 60 * 1000);
```

### React Hook Example

```javascript
import { useEffect, useState } from 'react';

function useCueFavicon(apiUrl) {
    const [error, setError] = useState(null);
    
    useEffect(() => {
        fetch(`${apiUrl}/gallery/latest`)
            .then(res => res.json())
            .then(data => {
                if (data.image_data_url) {
                    const link = document.querySelector("link[rel*='icon']") || 
                                document.createElement('link');
                    link.type = 'image/png';
                    link.rel = 'icon';
                    link.href = data.image_data_url;
                    document.head.appendChild(link);
                }
            })
            .catch(err => setError(err.message));
    }, [apiUrl]);
    
    return { error };
}
```

## API Endpoints

- `GET /gallery` - List all gallery items
  - Query params: `limit`, `offset`
  - Returns: `{ items: [...], total: number }`

- `GET /gallery/latest` - Get the latest generation with a random image
  - Returns: `{ item: {...}, selected_image: {...}, image_data_url: "data:..." }`

## CORS Configuration

The Cue API has CORS enabled for all origins by default. For production, you may want to restrict this in `backend/server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-website.com"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
``` 