#!/bin/bash
# Restore mysqldump from file
# Usage: ./restore.sh [backup_file]

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if a file is provided as argument
if [ -z "$1" ]; then
    echo "No backup file specified."
    echo "Available backups in $DIR/backups:"
    
    # List .sql files
    OPTIONS=($(ls "$DIR/backups"/*.sql 2>/dev/null))

    if [ ${#OPTIONS[@]} -eq 0 ]; then
        echo "No .sql backup files found in $DIR/backups."
        exit 1
    fi

    # Display menu
    PS3="Select a number to restore: "
    select FILE in "${OPTIONS[@]}"; do
        if [ -n "$FILE" ]; then
            BACKUP_FILE="$FILE"
            break
        else
            echo "Invalid selection. Try again."
        fi
    done
else
    BACKUP_FILE="$1"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: File '$BACKUP_FILE' not found."
    exit 1
fi

echo "Restoring database 'jobs' from $BACKUP_FILE..."

cat "$BACKUP_FILE" | docker exec -i -e MYSQL_PWD=rootPass ai-job-search-mysql \
    /usr/bin/mysql -u root jobs

if [ $? -eq 0 ]; then
    echo "Restore completed successfully."
else
    echo "Restore failed."
    exit 1
fi
