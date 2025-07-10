#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function runCommand(command, description) {
  console.log(`🔧 ${description}...`);
  try {
    execSync(command, { stdio: 'inherit' });
    return true;
  } catch (error) {
    console.error(`❌ ${description} failed:`, error.message);
    return false;
  }
}

function createSystemdService() {
  const serviceConfig = `[Unit]
Description=Cue Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Cue/backend
ExecStart=/root/.local/bin/uv run uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10
Environment=PATH=/root/.local/bin:$PATH
Environment=SEQUENTIAL_PROCESSING=true
EnvironmentFile=-/opt/Cue/.env

[Install]
WantedBy=multi-user.target
`;

  console.log('🔧 Creating systemd service...');
  fs.writeFileSync('/etc/systemd/system/cue-backend.service', serviceConfig);
  console.log('✅ Systemd service created');
}

function main() {
  console.log('🚀 Deploying Cue to Production...');

  // Copy nginx config
  if (!runCommand('sudo cp nginx-cue-simple.conf /etc/nginx/sites-available/cue.the-o.space', 'Configuring nginx')) {
    process.exit(1);
  }

  if (!runCommand('sudo ln -sf /etc/nginx/sites-available/cue.the-o.space /etc/nginx/sites-enabled/', 'Linking nginx config')) {
    process.exit(1);
  }

  // Test nginx config
  if (!runCommand('sudo nginx -t', 'Testing nginx configuration')) {
    console.log('❌ Nginx config error, aborting...');
    process.exit(1);
  }

  console.log('✅ Nginx config valid, reloading...');
  if (!runCommand('sudo systemctl reload nginx', 'Reloading nginx')) {
    process.exit(1);
  }

  // Create systemd service
  try {
    createSystemdService();
  } catch (error) {
    console.error('❌ Failed to create systemd service:', error.message);
    process.exit(1);
  }

  // Enable and start service
  if (!runCommand('sudo systemctl daemon-reload', 'Reloading systemd daemon')) {
    process.exit(1);
  }

  if (!runCommand('sudo systemctl enable cue-backend', 'Enabling cue-backend service')) {
    process.exit(1);
  }

  if (!runCommand('sudo systemctl restart cue-backend', 'Restarting cue-backend service')) {
    process.exit(1);
  }

  console.log('✅ Deployment complete!');
  console.log('🌐 Visit: https://cue.the-o.space');
  console.log('📊 Check backend: npm run status');
  console.log('🔍 Check logs: npm run logs');
  console.log('🔄 Restart services: npm run restart');
}

if (require.main === module) {
  main();
}

module.exports = { runCommand, createSystemdService }; 