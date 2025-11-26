#!/bin/bash

# Stop script on error
set -e

echo "🚀 Starting server provisioning..."

# 1. Update system
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# 2. Install dependencies
echo "🛠️ Installing dependencies..."
apt-get install -y apt-transport-https ca-certificates curl software-properties-common git ufw

# 3. Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed successfully"
else
    echo "✅ Docker is already installed"
fi

# 4. Install Docker Compose
echo "🐙 Installing Docker Compose..."
apt-get install -y docker-compose-plugin

# 5. Configure Firewall (UFW)
echo "🛡️ Configuring Firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
# Enable UFW non-interactively
echo "y" | ufw enable
echo "✅ Firewall configured"

# 6. Create project directory
echo "📂 Creating project directory..."
mkdir -p ~/homepage

echo "✨ Server provisioning completed! You are ready to deploy."
