#!/bin/bash
# Stop Celery worker and beat scheduler

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping Celery Workers${NC}\n"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check for PID files
if [ -f "logs/celery_worker.pid" ]; then
    WORKER_PID=$(cat logs/celery_worker.pid)
    echo -e "${YELLOW}Stopping Celery Worker (PID: $WORKER_PID)${NC}"
    kill -TERM $WORKER_PID 2>/dev/null || echo "  Worker already stopped"
    rm -f logs/celery_worker.pid
else
    echo -e "${YELLOW}No worker PID file found${NC}"
fi

if [ -f "logs/celery_beat.pid" ]; then
    BEAT_PID=$(cat logs/celery_beat.pid)
    echo -e "${YELLOW}Stopping Celery Beat (PID: $BEAT_PID)${NC}"
    kill -TERM $BEAT_PID 2>/dev/null || echo "  Beat already stopped"
    rm -f logs/celery_beat.pid
else
    echo -e "${YELLOW}No beat PID file found${NC}"
fi

# Wait for processes to stop
sleep 2

# Force kill if still running
pkill -f "celery.*app.tasks.celery_app" 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ Celery stopped${NC}"
