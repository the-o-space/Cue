#!/bin/bash

echo "🔧 Setting up Cue project..."

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx nodejs npm

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Setup backend
echo "🐍 Setting up backend..."
cd backend
uv sync
cd ..

# Setup frontend
echo "⚛️  Setting up frontend..."
cd frontend
npm install
cd ..

echo "✅ Setup complete!"
echo "🚀 Next steps:"
echo "   1. Set up DNS A record: cue.the-o.space -> 46.62.155.122"
echo "   2. Run: sudo certbot --nginx -d cue.the-o.space"
echo "   3. Run: ./deploy-production.sh" 