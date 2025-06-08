#!/bin/bash

# CodeGraph Docker Prerequisite Check
# This script validates the environment and dependencies before running docker-compose

set -e

echo "🐳 CodeGraph Docker Prerequisite Check"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track success/failure
ALL_CHECKS_PASSED=true

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        ALL_CHECKS_PASSED=false
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check 1: Docker is installed and running
echo
echo "1. Checking Docker..."
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_status 0 "Docker is installed and running (version: $DOCKER_VERSION)"
    else
        print_status 1 "Docker is installed but not running. Please start Docker Desktop."
    fi
else
    print_status 1 "Docker is not installed. Please install Docker Desktop."
fi

# Check 2: Docker Compose is available
echo
echo "2. Checking Docker Compose..."
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short)
    print_status 0 "Docker Compose is available (version: $COMPOSE_VERSION)"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
    print_status 0 "Docker Compose is available (version: $COMPOSE_VERSION)"
    print_warning "Using legacy docker-compose. Consider upgrading to 'docker compose'."
else
    print_status 1 "Docker Compose is not available. Please install Docker Compose."
fi

# Check 3: .env file exists
echo
echo "3. Checking environment configuration..."
if [ -f ".env" ]; then
    print_status 0 ".env file found"
    
    # Check required environment variables
    echo "   Validating required environment variables..."
    
    # Check Neo4j configuration
    if grep -q "^NEO4J_URI=" .env && [ -n "$(grep "^NEO4J_URI=" .env | cut -d'=' -f2-)" ]; then
        NEO4J_URI=$(grep "^NEO4J_URI=" .env | cut -d'=' -f2-)
        print_info "Neo4j URI: $NEO4J_URI"
    else
        print_status 1 "NEO4J_URI not set in .env file"
    fi
    
    if grep -q "^NEO4J_USERNAME=" .env && [ -n "$(grep "^NEO4J_USERNAME=" .env | cut -d'=' -f2-)" ]; then
        NEO4J_USERNAME=$(grep "^NEO4J_USERNAME=" .env | cut -d'=' -f2-)
        print_info "Neo4j Username: $NEO4J_USERNAME"
    else
        print_status 1 "NEO4J_USERNAME not set in .env file"
    fi
    
    if grep -q "^NEO4J_PASSWORD=" .env && [ -n "$(grep "^NEO4J_PASSWORD=" .env | cut -d'=' -f2-)" ]; then
        print_info "Neo4j Password: [CONFIGURED]"
    else
        print_status 1 "NEO4J_PASSWORD not set in .env file"
    fi
    
    # Check OpenAI configuration
    if grep -q "^OPENAI_API_KEY=" .env && [ -n "$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2-)" ]; then
        OPENAI_KEY=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2-)
        if [[ $OPENAI_KEY == sk-* ]]; then
            print_info "OpenAI API Key: [CONFIGURED]"
        else
            print_status 1 "OpenAI API Key format appears invalid (should start with 'sk-')"
        fi
    else
        print_status 1 "OPENAI_API_KEY not set in .env file"
    fi
    
else
    print_status 1 ".env file not found"
    echo
    print_info "Please create a .env file with the following required variables:"
    echo "NEO4J_URI=neo4j://neo4j:7687"
    echo "NEO4J_USERNAME=neo4j"
    echo "NEO4J_PASSWORD=your_password"
    echo "OPENAI_API_KEY=your_openai_api_key"
    echo ""
    print_info "Note: The .env file will be read at runtime, not copied into the container."
    echo ""
    print_info "You can copy from .env.example if it exists:"
    if [ -f ".env.example" ]; then
        echo "cp .env.example .env"
    fi
fi

# Check 4: Port availability
echo
echo "4. Checking port availability..."
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        # Check if it's already our Docker service
        PROCESS_INFO=$(lsof -Pi :$port -sTCP:LISTEN | grep -v COMMAND)
        if [[ "$PROCESS_INFO" == *"docker"* ]] || [[ "$PROCESS_INFO" == *"com.docker"* ]]; then
            print_warning "Port $port is in use by Docker (possibly previous CodeGraph instance)"
            print_info "Use 'cd docker && docker-compose down' to stop existing services"
        else
            print_status 1 "Port $port is already in use (needed for $service)"
            print_info "Stop the service using port $port or use: cd docker && docker-compose down"
        fi
    else
        print_status 0 "Port $port is available for $service"
    fi
}

check_port 8501 "Streamlit UI"
check_port 7687 "Neo4j Bolt"
check_port 7474 "Neo4j Browser"

# Check 5: Available disk space
echo
echo "5. Checking disk space..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')

# Simple check - if it contains 'T' (terabytes) or double-digit 'G' (gigabytes), we're good
if [[ "$AVAILABLE_SPACE" == *"T"* ]] || [[ "$AVAILABLE_SPACE" =~ ^[0-9][0-9]+.*G ]]; then
    print_status 0 "Sufficient disk space available (${AVAILABLE_SPACE} free)"
else
    print_warning "Disk space: ${AVAILABLE_SPACE} free. 2GB+ recommended for optimal performance."
fi

# Check 6: Memory availability
echo
echo "6. Checking memory..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    if [ $TOTAL_MEM -gt 4 ]; then
        print_status 0 "Sufficient memory available (${TOTAL_MEM}GB total)"
    else
        print_warning "Limited memory (${TOTAL_MEM}GB). 8GB+ recommended for optimal performance."
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print int($2/1024/1024)}')
    if [ $TOTAL_MEM -gt 4 ]; then
        print_status 0 "Sufficient memory available (${TOTAL_MEM}GB total)"
    else
        print_warning "Limited memory (${TOTAL_MEM}GB). 8GB+ recommended for optimal performance."
    fi
fi

# Summary
echo
echo "======================================"
if [ "$ALL_CHECKS_PASSED" = true ]; then
    echo -e "${GREEN}🎉 All prerequisite checks passed!${NC}"
    echo
    echo -e "${BLUE}You can now run:${NC}"
    echo "cd docker && docker-compose up -d"
    echo
    echo -e "${BLUE}To access the application:${NC}"
    echo "• CodeGraph UI: http://localhost:8501"
    echo "• Neo4j Browser: http://localhost:7474"
    echo
    echo -e "${BLUE}To stop the services:${NC}"
    echo "cd docker && docker-compose down"
    exit 0
else
    echo -e "${RED}❌ Some prerequisite checks failed!${NC}"
    echo
    echo -e "${YELLOW}Please fix the issues above before running docker-compose.${NC}"
    echo
    echo -e "${BLUE}Common solutions:${NC}"
    echo "• Install Docker Desktop and ensure it's running"
    echo "• Create .env file with required variables"
    echo "• Stop conflicting services: cd docker && docker-compose down"
    echo "• Free up disk space if needed"
    exit 1
fi 