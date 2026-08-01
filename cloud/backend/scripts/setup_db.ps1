# Setup PostgreSQL database and user for danke_robot
# Run as Administrator
$ErrorActionPreference = "Stop"

$pgData = "D:\develop\postgresql\data"
$pgBin = "D:\develop\postgresql\bin"
$pgHba = "$pgData\pg_hba.conf"

Write-Host "=== Setting up danke_robot database ==="

# 1. Backup pg_hba.conf
Copy-Item $pgHba "$pgHba.bak" -Force
Write-Host "Backed up pg_hba.conf"

# 2. Set to trust auth temporarily
(Get-Content $pgHba) -replace 'scram-sha-256', 'trust' | Set-Content $pgHba
Write-Host "Set pg_hba.conf to trust"

# 3. Restart PostgreSQL
Restart-Service -Name "postgresql-x64-17" -Force
Write-Host "PostgreSQL restarted"
Start-Sleep -Seconds 3

# 4. Create user and database
$env:PGPASSWORD = ""
& $pgBin\psql.exe -U postgres -h localhost -d postgres -c "CREATE USER parent WITH PASSWORD 'parent' CREATEDB;" 2>&1
& $pgBin\psql.exe -U postgres -h localhost -d postgres -c "CREATE DATABASE parent_db OWNER parent;" 2>&1
Write-Host "Created user parent and database parent_db"

# 5. Restore pg_hba.conf
Copy-Item "$pgHba.bak" $pgHba -Force
Write-Host "Restored pg_hba.conf"

# 6. Restart PostgreSQL
Restart-Service -Name "postgresql-x64-17" -Force
Write-Host "PostgreSQL restarted"

Write-Host "=== Done! ==="
Write-Host "Now run: cd d:/danke_robot/cloud/backend && alembic upgrade head"
