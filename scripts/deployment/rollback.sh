#!/bin/bash
# Rollback Script for RSS Feed Backend
# Usage: ./rollback.sh [backup_file]

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_FILE=${1:-""}
BACKUP_DIR="/backups"

echo "========================================="
echo "RSS Feed Backend Rollback"
echo "========================================="

# Function to list available backups
list_backups() {
    echo ""
    echo "Available backups:"
    echo "-----------------------------------"
    ls -lht $BACKUP_DIR/*.sql 2>/dev/null || echo "No backups found in $BACKUP_DIR"
    echo "-----------------------------------"
}

# Function to confirm action
confirm() {
    read -p "Are you sure you want to proceed? (yes/no): " response
    if [ "$response" != "yes" ]; then
        echo -e "${YELLOW}Rollback cancelled.${NC}"
        exit 0
    fi
}

# Step 1: Stop the application
echo ""
echo "Step 1: Stopping application..."
docker-compose -f docker-compose.prod.yml stop backend || {
    echo -e "${RED}Failed to stop application${NC}"
    exit 1
}
echo -e "${GREEN}✓ Application stopped${NC}"

# Step 2: List backups if no backup file provided
if [ -z "$BACKUP_FILE" ]; then
    list_backups
    echo ""
    read -p "Enter the backup file path to restore: " BACKUP_FILE
fi

# Step 3: Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    list_backups
    exit 1
fi

echo ""
echo "Rollback details:"
echo "  Backup file: $BACKUP_FILE"
echo "  Backup size: $(ls -lh $BACKUP_FILE | awk '{print $5}')"
echo "  Backup date: $(ls -l $BACKUP_FILE | awk '{print $6, $7, $8}')"
echo ""

confirm

# Step 4: Create pre-rollback backup
echo ""
echo "Step 2: Creating pre-rollback backup..."
PRE_ROLLBACK_BACKUP="$BACKUP_DIR/pre_rollback_$(date +%Y%m%d_%H%M%S).sql"
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$PRE_ROLLBACK_BACKUP" || {
    echo -e "${RED}Failed to create pre-rollback backup${NC}"
    exit 1
}
echo -e "${GREEN}✓ Pre-rollback backup created: $PRE_ROLLBACK_BACKUP${NC}"

# Step 5: Restore database
echo ""
echo "Step 3: Restoring database from backup..."
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < "$BACKUP_FILE" || {
    echo -e "${RED}Failed to restore database${NC}"
    echo -e "${YELLOW}You can restore the pre-rollback backup:${NC}"
    echo "  psql \$DATABASE_URL < $PRE_ROLLBACK_BACKUP"
    exit 1
}
echo -e "${GREEN}✓ Database restored${NC}"

# Step 6: Rollback application code (optional)
echo ""
echo "Step 4: Rolling back application code..."
read -p "Enter the Docker image tag to rollback to (or press Enter to use 'latest'): " IMAGE_TAG
IMAGE_TAG=${IMAGE_TAG:-latest}

export IMAGE_TAG
docker-compose -f docker-compose.prod.yml pull backend || {
    echo -e "${RED}Failed to pull Docker image${NC}"
    exit 1
}
echo -e "${GREEN}✓ Docker image pulled: $IMAGE_TAG${NC}"

# Step 7: Start application
echo ""
echo "Step 5: Starting application..."
docker-compose -f docker-compose.prod.yml up -d backend || {
    echo -e "${RED}Failed to start application${NC}"
    exit 1
}
echo -e "${GREEN}✓ Application started${NC}"

# Step 8: Wait for application to be ready
echo ""
echo "Step 6: Waiting for application to be ready..."
sleep 10

# Step 9: Health check
echo ""
echo "Step 7: Running health checks..."
./scripts/deployment/health_check.sh http://localhost:8000 || {
    echo -e "${RED}Health checks failed after rollback!${NC}"
    echo -e "${YELLOW}Please investigate immediately.${NC}"
    exit 1
}

# Success
echo ""
echo "========================================="
echo -e "${GREEN}Rollback completed successfully! ✓${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "  Database restored from: $BACKUP_FILE"
echo "  Pre-rollback backup saved: $PRE_ROLLBACK_BACKUP"
echo "  Application version: $IMAGE_TAG"
echo ""
echo "Next steps:"
echo "  1. Verify application functionality"
echo "  2. Check application logs: docker-compose -f docker-compose.prod.yml logs -f backend"
echo "  3. Monitor error rates"
echo "  4. Document rollback reason"
echo "  5. Schedule post-mortem meeting"
echo ""
