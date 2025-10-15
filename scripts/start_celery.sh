#!/bin/bash
# Start Celery worker and beat scheduler for RSS feed processing

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Celery Workers for RSS Feed Backend${NC}\n"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis is not running!${NC}"
    echo "Please start Redis first:"
    echo "  - macOS: brew services start redis"
    echo "  - Linux: sudo systemctl start redis"
    echo "  - Docker: docker-compose -f docker/docker-compose.dev.yml up -d redis"
    exit 1
fi

echo -e "${GREEN}✓ Redis is running${NC}\n"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${YELLOW}Virtual environment not found. Please create one first:${NC}"
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements-dev.txt"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Create log directory
mkdir -p logs

echo -e "${BLUE}Starting Celery components...${NC}\n"

# Option 1: Start in foreground (for development/debugging)
if [ "$1" == "--foreground" ]; then
    echo -e "${GREEN}Starting Celery Worker + Beat in foreground mode${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Start worker with beat in one process (development mode)
    celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --beat \
        --scheduler celery.beat:PersistentScheduler \
        --max-tasks-per-child=50 \
        --concurrency=4
    
# Option 2: Start as background daemons (default)
else
    echo -e "${GREEN}Starting Celery Worker (background)${NC}"
    celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --logfile=logs/celery_worker.log \
        --pidfile=logs/celery_worker.pid \
        --detach \
        --max-tasks-per-child=50 \
        --concurrency=4
    
    sleep 2
    
    echo -e "${GREEN}Starting Celery Beat Scheduler (background)${NC}"
    celery -A app.tasks.celery_app beat \
        --loglevel=info \
        --logfile=logs/celery_beat.log \
        --pidfile=logs/celery_beat.pid \
        --scheduler celery.beat:PersistentScheduler \
        --detach
    
    echo ""
    echo -e "${GREEN}✅ Celery started successfully!${NC}"
    echo ""
    echo "📊 Status:"
    echo "  Worker PID: $(cat logs/celery_worker.pid 2>/dev/null || echo 'Not found')"
    echo "  Beat PID: $(cat logs/celery_beat.pid 2>/dev/null || echo 'Not found')"
    echo ""
    echo "📝 Logs:"
    echo "  Worker: logs/celery_worker.log"
    echo "  Beat: logs/celery_beat.log"
    echo ""
    echo "🛑 To stop:"
    echo "  ./scripts/stop_celery.sh"
    echo ""
    echo "👀 To monitor:"
    echo "  tail -f logs/celery_worker.log"
    echo "  tail -f logs/celery_beat.log"
    echo ""
    echo "⏰ RSS feeds will be fetched every 15 minutes automatically"
fi
