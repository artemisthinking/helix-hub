#!/bin/bash
# 🇨🇭 Helix Hub Enterprise Sanity Check Script
# SwissLife-inspired comprehensive system validation
# Run this anytime to verify your enterprise banking platform is running with Swiss precision!

set -e  # Exit on any error

# Colors for beautiful output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Emojis for Swiss precision
CHECK="✅"
CROSS="❌"
INFO="ℹ️"
ROCKET="🚀"
SWISS="🇨🇭"
BANK="🏦"
MONEY="💰"
GEAR="⚙️"

echo -e "${WHITE}${SWISS}=====================================================================${SWISS}${NC}"
echo -e "${WHITE}     HELIX HUB ENTERPRISE SANITY CHECK - SWISSLIFE EDITION${NC}"
echo -e "${WHITE}     Comprehensive system validation with Swiss precision${NC}"
echo -e "${WHITE}${SWISS}=====================================================================${SWISS}${NC}"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to make HTTP request with error handling
make_request() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"
    
    echo -ne "${INFO} Testing: $description..."
    
    if command_exists curl; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url" 2>/dev/null)
        status_code="${response: -3}"
        
        if [ "$status_code" = "$expected_status" ]; then
            echo -e " ${CHECK} ${GREEN}OK (${status_code})${NC}"
            return 0
        else
            echo -e " ${CROSS} ${RED}FAILED (${status_code})${NC}"
            return 1
        fi
    else
        echo -e " ${CROSS} ${RED}curl not found${NC}"
        return 1
    fi
}

# Function to test authenticated endpoint
test_authenticated_endpoint() {
    local endpoint="$1"
    local description="$2"
    
    if [ -n "$TOKEN" ]; then
        make_request "http://localhost:5000$endpoint" 200 "$description (authenticated)"
    else
        echo -e "${YELLOW} ⚠️  Skipping $description - no auth token${NC}"
    fi
}

echo -e "${BLUE}${GEAR} STEP 1: Docker Container Health Check${NC}"
echo "----------------------------------------"

# Check if containers are running
if command_exists docker; then
    running_containers=$(docker ps --format "{{.Names}}" | grep helix-mvp || echo "")
    if [ -n "$running_containers" ]; then
        echo -e "${CHECK} ${GREEN}Docker containers running:${NC}"
        echo "$running_containers" | while read container; do
            echo -e "   ${ROCKET} $container"
        done
    else
        echo -e "${CROSS} ${RED}No Helix containers running!${NC}"
        echo -e "${INFO} Run: ${YELLOW}docker-compose up -d${NC}"
        exit 1
    fi
else
    echo -e "${CROSS} ${RED}Docker not found${NC}"
    exit 1
fi
echo

echo -e "${BLUE}${BANK} STEP 2: Core API Health Checks${NC}"
echo "----------------------------------------"

# Basic health checks
make_request "http://localhost:5000/" 302 "Root endpoint (redirect to dashboard)"
make_request "http://localhost:5000/api/system/health" 200 "System health"
make_request "http://localhost:5000/dashboard" 200 "Dashboard"
echo

echo -e "${BLUE}${SWISS} STEP 3: SwissLife Enterprise Routing API${NC}"
echo "----------------------------------------"

# Test department discovery
if make_request "http://localhost:5000/api/files/departments" 200 "Department discovery"; then
    echo -e "${INFO} ${CYAN}Available departments:${NC}"
    if [ -f /tmp/response.json ]; then
        if command_exists jq; then
            jq -r '.departments[] | "   \(.emoji) \(.code): \(.name) - Processes: \(.processes | join(", "))"' /tmp/response.json 2>/dev/null || cat /tmp/response.json
        else
            echo -e "${YELLOW}   (Install jq for prettier output)${NC}"
            cat /tmp/response.json | head -20
        fi
    fi
fi
echo

# Test routing codes
if make_request "http://localhost:5000/api/files/routing-codes" 200 "Routing codes discovery"; then
    if [ -f /tmp/response.json ] && command_exists jq; then
        total_codes=$(jq '.routing_codes | length' /tmp/response.json 2>/dev/null || echo "unknown")
        echo -e "${INFO} ${CYAN}Total routing combinations: ${WHITE}$total_codes${NC}"
        echo -e "${INFO} ${CYAN}Sample routing codes:${NC}"
        jq -r '.routing_codes[:5][] | "   ✓ \(.routing_code) - \(.description)"' /tmp/response.json 2>/dev/null || echo "   (Error parsing response)"
        echo -e "   ${PURPLE}... and $((total_codes - 5)) more combinations!${NC}"
    fi
fi
echo

echo -e "${BLUE}${MONEY} STEP 4: Authentication & Security${NC}"
echo "----------------------------------------"

# Test authentication
echo -ne "${INFO} Testing JWT authentication..."
if command_exists curl; then
    auth_response=$(curl -s -X POST "http://localhost:5000/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "adminpass"}' 2>/dev/null)
    
    if command_exists jq; then
        TOKEN=$(echo "$auth_response" | jq -r '.access_token' 2>/dev/null)
        if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
            echo -e " ${CHECK} ${GREEN}Authentication successful${NC}"
            echo -e "${INFO} ${CYAN}Token: ${TOKEN:0:50}...${NC}"
        else
            echo -e " ${CROSS} ${RED}Authentication failed${NC}"
            TOKEN=""
        fi
    else
        echo -e " ${YELLOW}(Install jq to parse auth response)${NC}"
        TOKEN=""
    fi
else
    echo -e " ${CROSS} ${RED}curl not available${NC}"
    TOKEN=""
fi
echo

echo -e "${BLUE}${GEAR} STEP 5: Protected Endpoints (if authenticated)${NC}"
echo "----------------------------------------"

if [ -n "$TOKEN" ]; then
    # Test protected endpoints
    echo -ne "${INFO} Testing job management endpoint..."
    if curl -s -H "Authorization: Bearer $TOKEN" \
            -H "accept: application/json" \
            "http://localhost:5000/api/files/jobs" >/tmp/jobs_response.json 2>/dev/null; then
        echo -e " ${CHECK} ${GREEN}Jobs endpoint accessible${NC}"
        
        if command_exists jq && [ -f /tmp/jobs_response.json ]; then
            job_count=$(jq -r '.total_count // 0' /tmp/jobs_response.json 2>/dev/null)
            message=$(jq -r '.message // "No message"' /tmp/jobs_response.json 2>/dev/null)
            echo -e "${INFO} ${CYAN}$message${NC}"
        fi
    else
        echo -e " ${CROSS} ${RED}Jobs endpoint failed${NC}"
    fi
else
    echo -e "${YELLOW} ⚠️  Skipping protected endpoint tests - no authentication${NC}"
fi
echo

echo -e "${BLUE}${ROCKET} STEP 6: File Processing Status${NC}"
echo "----------------------------------------"

# Check SFTP directory
sftp_dir="./sftp/incoming"
if [ -d "$sftp_dir" ]; then
    file_count=$(find "$sftp_dir" -type f | wc -l)
    echo -e "${CHECK} ${GREEN}SFTP directory exists: $sftp_dir${NC}"
    echo -e "${INFO} ${CYAN}Files in SFTP directory: $file_count${NC}"
    
    if [ "$file_count" -gt 0 ]; then
        echo -e "${INFO} ${CYAN}Recent files:${NC}"
        find "$sftp_dir" -type f -printf "   📄 %f (%TY-%Tm-%Td %TH:%TM)\n" | head -5
    fi
else
    echo -e "${YELLOW} ⚠️  SFTP directory not found: $sftp_dir${NC}"
fi

# Check processed files
data_dir="./helix-core/data"
if [ -d "$data_dir" ]; then
    processed_count=$(find "$data_dir" -name "*_Processed_*" -type f 2>/dev/null | wc -l)
    echo -e "${CHECK} ${GREEN}Data directory exists: $data_dir${NC}"
    echo -e "${INFO} ${CYAN}Processed files found: $processed_count${NC}"
else
    echo -e "${YELLOW} ⚠️  Data directory not found: $data_dir${NC}"
fi
echo

echo -e "${BLUE}${GEAR} STEP 7: System Performance Check${NC}"
echo "----------------------------------------"

# Check system resources
if command_exists docker; then
    echo -e "${INFO} ${CYAN}Docker container resource usage:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep helix-mvp || echo "   No stats available"
fi
echo

echo -e "${BLUE}${INFO} STEP 8: Quick Links & Information${NC}"
echo "----------------------------------------"
echo -e "${ROCKET} ${CYAN}Dashboard:${NC}         http://localhost:5000/dashboard"
echo -e "${ROCKET} ${CYAN}Swagger API:${NC}       http://localhost:5000/swagger/"
echo -e "${ROCKET} ${CYAN}Health Check:${NC}      http://localhost:5000/api/system/health"
echo -e "${ROCKET} ${CYAN}Departments:${NC}       http://localhost:5000/api/files/departments"
echo -e "${ROCKET} ${CYAN}Routing Codes:${NC}     http://localhost:5000/api/files/routing-codes"
echo -e "${ROCKET} ${CYAN}Traefik Dashboard:${NC} http://localhost:8080/"
echo

echo -e "${WHITE}${SWISS}=====================================================================${SWISS}${NC}"
echo -e "${WHITE}  🎉 ${GREEN}HELIX HUB ENTERPRISE SANITY CHECK COMPLETE!${NC}"
echo -e "${WHITE}     Swiss precision validated - ready for banking domination! ${MONEY}${NC}"
echo -e "${WHITE}${SWISS}=====================================================================${SWISS}${NC}"

# Cleanup
rm -f /tmp/response.json /tmp/jobs_response.json

echo
echo -e "${INFO} ${CYAN}Pro Tips:${NC}"
echo -e "   • Run this script anytime: ${YELLOW}./sanity-check.sh${NC}"
echo -e "   • For file upload test: ${YELLOW}./test_swiss_api.sh${NC}"
echo -e "   • View logs: ${YELLOW}docker-compose logs -f helix-core${NC}"
echo -e "   • Restart system: ${YELLOW}docker-compose restart${NC}"
echo
