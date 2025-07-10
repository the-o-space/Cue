/**
 * GitHub webhook handler for updating website favicon with Cue gallery images.
 * 
 * This can be deployed as a Vercel/Netlify function or adapted for other platforms.
 * It listens for GitHub push events and updates the favicon with a random image
 * from the latest Cue generation.
 */

// Vercel example
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const CUE_API_URL = process.env.CUE_API_URL || 'http://localhost:8001';
  
  // Parse GitHub webhook event
  const event = req.headers['x-github-event'];
  if (event !== 'push') {
    return res.status(200).json({ status: 'ignored', reason: 'not a push event' });
  }

  const payload = req.body;
  
  // Check if gallery was updated
  const galleryUpdated = payload.commits?.some(commit => 
    [...(commit.added || []), ...(commit.modified || [])].some(file => 
      file.startsWith('gallery/')
    )
  );

  if (!galleryUpdated) {
    return res.status(200).json({ status: 'ignored', reason: 'no gallery updates' });
  }

  try {
    // Fetch latest generation from Cue API
    const response = await fetch(`${CUE_API_URL}/gallery/latest`);
    
    if (!response.ok) {
      return res.status(500).json({ status: 'error', reason: 'failed to fetch latest generation' });
    }

    const latestData = await response.json();
    
    if (!latestData.image_data_url) {
      return res.status(500).json({ status: 'error', reason: 'no image data in response' });
    }

    // Return the data for client-side favicon update
    return res.status(200).json({
      status: 'success',
      generationId: latestData.item?.id || 'unknown',
      textPreview: (latestData.item?.text || '').substring(0, 50) + '...',
      imageDataUrl: latestData.image_data_url
    });

  } catch (error) {
    console.error('Webhook error:', error);
    return res.status(500).json({ status: 'error', reason: error.message });
  }
}

// Standalone fetch function for manual usage
export async function fetchLatestGalleryImage(apiUrl = 'http://localhost:8001') {
  try {
    const response = await fetch(`${apiUrl}/gallery/latest`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching latest gallery image:', error);
    return null;
  }
}

// Client-side favicon updater (include in your frontend)
export function updateFaviconFromDataUrl(dataUrl) {
  // Remove existing favicons
  const existingLinks = document.querySelectorAll("link[rel*='icon']");
  existingLinks.forEach(link => link.remove());

  // Create new favicon link
  const link = document.createElement('link');
  link.type = 'image/png';
  link.rel = 'icon';
  link.href = dataUrl;
  document.head.appendChild(link);

  // Also update apple-touch-icon if needed
  const appleLink = document.createElement('link');
  appleLink.rel = 'apple-touch-icon';
  appleLink.href = dataUrl;
  document.head.appendChild(appleLink);
}

// Example usage in a client app
export async function updateFaviconFromCueGallery(apiUrl = 'http://localhost:8001') {
  const data = await fetchLatestGalleryImage(apiUrl);
  if (data && data.image_data_url) {
    updateFaviconFromDataUrl(data.image_data_url);
    return true;
  }
  return false;
} 