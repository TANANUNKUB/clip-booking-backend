#!/bin/bash

# Clip Booking API Setup Script
# This script helps you set up the Clip Booking API with Docker

set -e

echo "🚀 Clip Booking API Setup"
echo "=========================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your Supabase credentials:"
    echo "   - SUPABASE_URL: Your Supabase project URL"
    echo "   - SUPABASE_ANON_KEY: Your Supabase anonymous key"
    echo ""
    echo "After editing .env, run this script again."
    exit 0
fi

# Check if .env has been configured
if grep -q "your_supabase_project_url_here" .env; then
    echo "⚠️  Please configure your Supabase credentials in .env file first."
    echo "   - SUPABASE_URL: Your Supabase project URL"
    echo "   - SUPABASE_ANON_KEY: Your Supabase anonymous key"
    exit 1
fi

echo "✅ Environment variables are configured"

# Build and run the application
echo "🐳 Building and starting the application..."
docker-compose up --build -d

echo ""
echo "✅ Application is starting up!"
echo ""
echo "📋 Next steps:"
echo "1. Wait a few seconds for the application to start"
echo "2. Visit http://localhost:8000/docs for API documentation"
echo "3. Run 'python test_api.py' to test the API endpoints"
echo ""
echo "📊 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop application: docker-compose down"
echo "   - Restart application: docker-compose restart"
echo ""
echo "�� Setup complete!" 