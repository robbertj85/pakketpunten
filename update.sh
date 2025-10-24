#!/bin/bash

# Weekly update script for pakketpunten data
# This script activates the virtual environment and runs the weekly update

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Pakketpunten Weekly Update Script                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}→${NC} Activating virtual environment..."
source venv/bin/activate

# Check if weekly_update.py exists
if [ ! -f "weekly_update.py" ]; then
    echo "❌ weekly_update.py not found!"
    exit 1
fi

# Run the weekly update with logging
LOG_FILE="weekly_update_$(date +%Y%m%d_%H%M%S).log"
echo -e "${GREEN}→${NC} Running weekly update..."
echo -e "${GREEN}→${NC} Log file: $LOG_FILE"
echo ""

python weekly_update.py 2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Weekly update completed successfully!${NC}"
else
    echo ""
    echo -e "⚠️  Weekly update completed with errors (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
