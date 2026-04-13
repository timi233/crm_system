#!/bin/bash

# CRM System Quick Start and Validation Script
# This script automates the entire setup and validation process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "🚀 CRM System Quick Start Script"
echo "================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
port_available() {
    lsof -i :$1 > /dev/null 2>&1
    [ $? -ne 0 ]
}

# Function to clean up previous processes
cleanup() {
    echo "🧹 Cleaning up previous processes..."
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "react-scripts" 2>/dev/null || true
    pkill -f "node" 2>/dev/null || true
}

# Function to setup database
setup_database() {
    echo "💾 Setting up PostgreSQL database..."
    
    # Check if PostgreSQL is running
    if ! systemctl is-active --quiet postgresql; then
        echo "⚠️  PostgreSQL is not running. Starting service..."
        sudo systemctl start postgresql
    fi
    
    # Create database and user
    sudo -u postgres psql << EOF
CREATE USER IF NOT EXISTS crm_admin WITH PASSWORD 'crm_secure_pw_2024';
CREATE DATABASE IF NOT EXISTS crm_db OWNER crm_admin;
\q
EOF
    
    echo "✅ Database setup completed"
}

# Function to setup backend
setup_backend() {
    echo "⚙️  Setting up backend..."
    cd "$PROJECT_ROOT/backend"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Create .env file
    cat > .env << EOF
# Environment configuration for the CRM system
# Database (PostgreSQL) connection
POSTGRES_USER=crm_admin
POSTGRES_PASSWORD=crm_secure_pw_2024
POSTGRES_DB=crm_db
DB_HOST=localhost
DB_PORT=5432

# Redis cache
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT / security
JWT_SECRET_KEY=RkRUvPjY8vaJlLSeVCbxEHPfnOpGH9vg-k1QX5AD2E0
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# FastAPI port (for local/dev; docker-compose uses container ports)
APP_PORT=8000

# CORS - allow local frontend
ALLOWED_ORIGINS=http://localhost:3002,http://127.0.0.1:3002

# Database URL
DATABASE_URL=postgresql+asyncpg://crm_admin:crm_secure_pw_2024@localhost:5432/crm_db

# Feishu OAuth configuration
FEISHU_APP_ID=cli_a9f5450adc781bd2
FEISHU_APP_SECRET=waXI7c1MdjbQ9INhPQ1cUb0UpBI82pby
FEISHU_REDIRECT_URI=http://localhost:3002/auth/feishu/callback
EOF
    
    # Initialize database
    python reset_db.py
    
    echo "✅ Backend setup completed"
}

# Function to setup frontend
setup_frontend() {
    echo "🌐 Setting up frontend..."
    cd "$PROJECT_ROOT/frontend"
    
    # Install dependencies
    npm install
    
    # Create .env.local file
    cat > .env.local << EOF
REACT_APP_API_URL=http://localhost:8000
EOF
    
    echo "✅ Frontend setup completed"
}

# Function to start services
start_services() {
    echo "🚀 Starting services..."
    
    # Start backend in background
    cd "$PROJECT_ROOT/backend"
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 5
    
    # Start frontend in background  
    cd "$PROJECT_ROOT/frontend"
    PORT=3002 npm start &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    sleep 10
    
    echo "✅ Services started"
    echo "   Backend PID: $BACKEND_PID"
    echo "   Frontend PID: $FRONTEND_PID"
}

# Function to validate system
validate_system() {
    echo "🔍 Validating system functionality..."
    
    # Test health check
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo "✅ Health check passed"
    else
        echo "❌ Health check failed"
        return 1
    fi
    
    # Get auth token
    AUTH_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login -d "username=admin@example.com&password=admin123")
    AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$AUTH_TOKEN" ] || [ "$AUTH_TOKEN" = "null" ]; then
        echo "❌ Authentication failed"
        return 1
    fi
    echo "✅ Authentication successful"
    
    # Test core APIs
    APIS=("/users" "/leads" "/opportunities" "/dashboard/summary" "/alert-rules")
    for api in "${APIS[@]}"; do
        if curl -s -H "Authorization: Bearer $AUTH_TOKEN" http://localhost:8000$api | jq '.' > /dev/null 2>&1; then
            echo "✅ API $api working"
        else
            echo "❌ API $api failed"
            return 1
        fi
    done
    
    echo "✅ All validation tests passed!"
    return 0
}

# Main execution
main() {
    cleanup
    setup_database
    setup_backend
    setup_frontend
    start_services
    
    # Validate after a short delay
    sleep 15
    if validate_system; then
        echo ""
        echo "🎉 CRM System is ready!"
        echo ""
        echo "📋 Usage Instructions:"
        echo "   Web Interface: http://localhost:3002"
        echo "   API Documentation: http://localhost:8000/docs"
        echo ""
        echo "🔑 Login Credentials:"
        echo "   Email: admin@example.com"
        echo "   Password: admin123"
        echo ""
        echo "📚 Documentation:"
        echo "   Deployment Guide: $PROJECT_ROOT/docs/deployment-guide.md"
        echo "   Troubleshooting: $PROJECT_ROOT/docs/troubleshooting-guide.md"
        echo "   Architecture: $PROJECT_ROOT/docs/architecture-design.md"
        
        # Keep services running
        wait
    else
        echo "❌ System validation failed. Please check the logs above."
        exit 1
    fi
}

# Handle interrupts
trap 'echo "🛑 Stopping services..."; pkill -P $$; exit 0' INT TERM

# Run main function
main