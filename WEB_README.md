# Cue Web Application

A minimalistic web interface for Cue - transform text into abstract art through sentiment analysis.

## Structure

```
/opt/Cue/
├── backend/
│   └── server.py        # FastAPI backend
├── frontend/
│   ├── src/            # React source files
│   ├── package.json    # Frontend dependencies
│   └── vite.config.ts  # Vite configuration
└── *.py                # Existing Cue modules
```

## Quick Start

1. **Setup:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Run locally:**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

   Visit http://localhost:5173

## Production Deployment

1. **Deploy to production:**
   ```bash
   chmod +x deploy-production.sh
   ./deploy-production.sh
   ```

2. **SSL Certificate (first time only):**
   ```bash
   sudo certbot --nginx -d cue.the-o.space
   ```

## Architecture

- **Frontend**: React + Vite + Tailwind CSS
  - Single page application
  - Minimalistic design
  - No authentication required
  
- **Backend**: FastAPI + Existing Cue modules
  - `/api/generate` - Generate art from text
  - Returns base64-encoded images
  - No data persistence

## Development

- Frontend dev server: `cd frontend && npm run dev`
- Backend dev server: `cd backend && uvicorn server:app --reload`

## Notes

- Images are generated on-demand and not saved
- No user accounts or authentication
- Public access for everyone
- Minimal dependencies and complexity 