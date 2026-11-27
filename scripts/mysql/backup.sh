#!/bin/bash
# Backup mysqldump to scripts/mysql
# Usage: ./backup.sh

# Get directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_DIR="$DIR/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/$(date +%Y%m%d_%H%M)_backup.sql"

echo "Backing up database 'jobs' to $BACKUP_FILE..."

# Use docker exec with mysqldump
# Suppress warnings: GTID, password security
docker exec -i -e MYSQL_PWD=rootPass ai-job-search-mysql \
    /usr/bin/mysqldump -u root \
    --single-transaction \
    --routines --triggers --events \
    --set-gtid-purged=OFF \
    jobs > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup completed successfully."
else
    echo "Backup failed."
    exit 1
fi
