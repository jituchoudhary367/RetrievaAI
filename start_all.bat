@echo off
echo Starting Qdrant...
start "Qdrant" /D "%~dp0qdrant" qdrant.exe

echo Starting Redis...
start "Redis" /D "%~dp0redis" redis-server.exe

echo Starting Backend API...
start "Backend API" /D "%~dp0backend" cmd /k ".\.venv\Scripts\python.exe run.py"

echo Starting Frontend Dev Server...
start "Frontend Dev Server" /D "%~dp0frontend" cmd /k "npm run dev"

echo ==========================================
echo All services have been launched!
echo They are running in separate windows.
echo Close those windows to stop the services.
echo ==========================================
pause
