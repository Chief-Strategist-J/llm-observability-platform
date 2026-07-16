#!/bin/bash
set -e

# Color variables
GREEN='\033[0;32m'
BLUE='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}      Automated Cron Installation Helper      ${NC}"
echo -e "${BLUE}===============================================${NC}"

if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}[x] Backup script not found at: $BACKUP_SCRIPT${NC}"
    exit 1
fi

chmod +x "$BACKUP_SCRIPT"

# Formulate the cron line
CRON_JOB="0 0 * * * cd $SCRIPT_DIR && ./backup.sh > /dev/null 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -qF "$BACKUP_SCRIPT"; then
    echo -e "${GREEN}[✓] Backup cron job is already installed in crontab.${NC}"
else
    # Install new cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}[✓] Backup cron job successfully installed in crontab!${NC}"
    echo -e "${BLUE}It will run automatically every day at midnight (00:00).${NC}"
fi
