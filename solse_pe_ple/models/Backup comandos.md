# Sacar backup
wget --post-data 'master_pwd=CLAVEMAESTRAODOO&name=NOMBRE_BD&backup_format=zip' -O ruta_y_nombre_guardar_backup.zip http://localhost:8069/web/database/backup

: Si el puerto donde corre odoo es diferente igual cambiar en las lineas de arriba

# Restaurar backup
curl -F 'master_pwd=CLAVEMAESTRAODOO' -F backup_file=@/home/ubuntu/ruta_y_nombre_guardar_backup.zip -F 'copy=true' -F 'name=NOMBRE_BD' http://localhost:8069/web/database/restore