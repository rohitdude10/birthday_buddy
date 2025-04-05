#!/bin/bash

# Production setup script for Birthday Buddy app
# This script prepares the environment for production

# Exit on any error
set -e

echo "🚀 Setting up Birthday Buddy for production..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from example..."
    cp .env.example .env
    
    # Generate secure random keys
    SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
    JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
    
    # Set production environment
    sed -i "s/ENV=development/ENV=production/" .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env
    
    echo "⚠️ Please update your .env file with database credentials"
else
    echo "✅ .env file already exists"
fi

# Create the instance directory if it doesn't exist
if [ ! -d "instance" ]; then
    echo "📁 Creating instance directory..."
    mkdir -p instance
fi

# Initialize database
echo "🗃️ Initializing database..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"

echo "🔒 Setting file permissions..."
chmod -R 755 .
chmod -R 700 instance

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your database in the .env file"
echo "2. Set up your web server (Nginx, Apache) as a reverse proxy"
echo "3. Start the application using: gunicorn wsgi:app"
echo ""
echo "Happy birthday tracking! 🎂" 