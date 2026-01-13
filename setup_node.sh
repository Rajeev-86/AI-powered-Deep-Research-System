#!/bin/bash

# Setup script for Node.js 20+ using NVM

echo "========================================"
echo "📦 Installing Node.js 20+ with NVM"
echo "========================================"
echo ""

# Check if NVM already installed
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    echo "✅ NVM already installed"
    source "$HOME/.nvm/nvm.sh"
else
    echo "📥 Installing NVM..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    
    # Load NVM
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

# Install Node.js 20
echo ""
echo "📥 Installing Node.js 20 LTS..."
nvm install 20
nvm use 20
nvm alias default 20

echo ""
echo "========================================"
echo "✅ Node.js Setup Complete!"
echo "========================================"
node --version
npm --version
echo ""
echo "💡 To use this Node version in future terminals, add to ~/.bashrc:"
echo '   export NVM_DIR="$HOME/.nvm"'
echo '   [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"'
echo ""
