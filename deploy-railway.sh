#!/bin/bash

# Polymarket Trading Bot - Railway Deployment Script
# Deploys backend and frontend as separate Railway services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Polymarket Trading Bot - Railway Deploy${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Railway CLI is not installed.${NC}"
    echo -e "Install it with: ${YELLOW}npm install -g @railway/cli${NC}"
    echo -e "Or: ${YELLOW}brew install railway${NC}"
    exit 1
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Railway. Logging in...${NC}"
    railway login
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_dir=$2

    echo ""
    echo -e "${GREEN}Deploying $service_name...${NC}"
    cd "$service_dir"

    # Check if linked to a project
    if ! railway status &> /dev/null; then
        echo -e "${YELLOW}No Railway project linked. Creating new service...${NC}"
        railway link
    fi

    # Deploy
    railway up --detach

    echo -e "${GREEN}$service_name deployed!${NC}"
}

# Menu
echo -e "Select deployment option:"
echo -e "  ${YELLOW}1)${NC} Deploy Backend only"
echo -e "  ${YELLOW}2)${NC} Deploy Frontend only"
echo -e "  ${YELLOW}3)${NC} Deploy Both (Backend + Frontend)"
echo -e "  ${YELLOW}4)${NC} Deploy Combined (Single container)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        deploy_service "Backend" "$SCRIPT_DIR/backend"
        ;;
    2)
        deploy_service "Frontend" "$SCRIPT_DIR/frontend"
        ;;
    3)
        deploy_service "Backend" "$SCRIPT_DIR/backend"
        deploy_service "Frontend" "$SCRIPT_DIR/frontend"
        echo ""
        echo -e "${YELLOW}Note: Set NEXT_PUBLIC_API_URL in Frontend to point to Backend URL${NC}"
        ;;
    4)
        echo -e "${GREEN}Deploying combined container...${NC}"
        cd "$SCRIPT_DIR"
        railway up --detach
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment initiated!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Run ${YELLOW}railway logs${NC} to see deployment logs"
echo -e "Run ${YELLOW}railway open${NC} to open the Railway dashboard"
echo ""

# Show environment variables reminder
echo -e "${YELLOW}Remember to set these environment variables in Railway:${NC}"
echo ""
echo -e "${BLUE}Backend:${NC}"
echo "  SECRET_KEY=your-secret-key-here"
echo "  DATABASE_URL=sqlite:///./data/polymarket.db"
echo "  OPENAI_API_KEY=your-openai-key (optional)"
echo "  QDRANT_URL=your-qdrant-url (optional)"
echo "  QDRANT_API_KEY=your-qdrant-key (optional)"
echo ""
echo -e "${BLUE}Frontend:${NC}"
echo "  NEXT_PUBLIC_API_URL=https://your-backend.railway.app"
echo "  NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app/ws"
echo ""
