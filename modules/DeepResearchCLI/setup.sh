#!/bin/bash

echo "🔍 Setting up MASS Deep Research CLI..."

# Check Node.js version
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18.0.0 or higher."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18.0.0 or higher is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Install dependencies
echo "📦 Installing dependencies..."
if command -v yarn &> /dev/null; then
    yarn install
else
    npm install
fi

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check if .env exists, if not copy from example
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your API keys and configuration."
else
    echo "✅ .env file already exists"
fi

# Build the project
echo "🔨 Building TypeScript project..."
if command -v yarn &> /dev/null; then
    yarn build
else
    npm run build
fi

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build completed successfully"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p research_data
mkdir -p cli/result

# Make the CLI executable
chmod +x dist/index.js

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit the .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Start your first research:"
echo "   npm start"
echo "   # or"
echo "   yarn start"
echo ""
echo "3. View available commands:"
echo "   npm start -- --help"
echo ""
echo "📚 For more information, see README.md"
echo ""