#!/bin/bash
BACKUP_DIR=/home/pytc/crm_system/backups
DATE=$(date +%Y%m%d_%H%M%S)
docker exec crm_system-db-1 pg_dump -U crm_user -d crm_db -F c -f /tmp/crm_backup.dump
docker cp crm_system-db-1:/tmp/crm_backup.dump $BACKUP_DIR/crm_backup_$DATE.dump
docker exec crm_system-db-1 rm /tmp/crm_backup.dump
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
echo "[$DATE] Backup completed: crm_backup_$DATE.dump" >> $BACKUP_DIR/backup.log