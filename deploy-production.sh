#!/bin/bash

echo "🚀 Deploying Cue to Production..."

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm run build
cd ..

# Copy nginx config
echo "⚙️  Configuring nginx..."
sudo cp nginx-cue-simple.conf /etc/nginx/sites-available/cue.the-o.space
sudo ln -sf /etc/nginx/sites-available/cue.the-o.space /etc/nginx/sites-enabled/

# Test nginx config
echo "🔧 Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config valid, reloading..."
    sudo systemctl reload nginx
else
    echo "❌ Nginx config error, aborting..."
    exit 1
fi

# Create systemd service for backend
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/cue-backend.service > /dev/null <<EOF
[Unit]
Description=Cue Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Cue/backend
ExecStart=/root/.local/bin/uv run uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10
Environment=PATH=/root/.local/bin:\$PATH

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cue-backend
sudo systemctl restart cue-backend

echo "✅ Deployment complete!"
echo "🌐 Visit: https://cue.the-o.space"
echo "📊 Check backend: sudo systemctl status cue-backend"
echo "🔍 Check logs: sudo journalctl -u cue-backend -f" 