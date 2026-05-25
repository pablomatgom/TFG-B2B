@echo off
setlocal enabledelayedexpansion
title TFG-B2B — Full Stack

:: Always run from the project root regardless of where it was launched from
cd /d "%~dp0"

echo.
echo  ==========================================
echo   TFG-B2B ^| Full Stack Launcher
echo  ==========================================
echo.

:: ── 1. Check Docker ─────────────────────────────────────────────────────────
echo  [1/5] Checking Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Docker Desktop is not running.
    echo  Please start Docker Desktop and try again.
    echo.
    pause & exit /b 1
)
echo         OK

:: ── 2. Start Neo4j ──────────────────────────────────────────────────────────
echo  [2/5] Starting Neo4j container...
docker compose up -d
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: docker compose up failed.
    echo.
    pause & exit /b 1
)
echo         OK

:: ── 3. Wait for Neo4j HTTP ──────────────────────────────────────────────────
echo  [3/5] Waiting for Neo4j...
echo        (first boot downloads GDS plugin - may take 1-2 min)
echo.
set /a dots=0
:poll_neo4j
curl -s -o nul -w "%%{http_code}" http://localhost:7474 2>nul | find "200" >nul 2>&1
if %errorlevel% neq 0 (
    set /a dots+=1
    if !dots! gtr 60 (
        echo.
        echo  TIMEOUT: Neo4j did not start. Check: docker compose logs neo4j
        echo.
        pause & exit /b 1
    )
    timeout /t 3 /nobreak >nul
    <nul set /p "=."
    goto poll_neo4j
)
echo  Ready!

:: ── 4. Start FastAPI backend ─────────────────────────────────────────────────
echo  [4/5] Starting FastAPI backend (port 8000)...
start "TFG-B2B Backend" cmd /k ".\.venv\Scripts\activate.bat && python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 4 /nobreak >nul
echo         OK

:: ── 5. Start Next.js frontend ────────────────────────────────────────────────
echo  [5/5] Starting Next.js frontend (port 3000)...
start "TFG-B2B Frontend" cmd /k "cd frontend && npm run dev"
echo         OK (compiling - takes ~10s on first run)

:: ── Done ─────────────────────────────────────────────────────────────────────
echo.
echo  ==========================================
echo   All services are up!
echo.
echo   Neo4j    : http://localhost:7474
echo   API docs : http://localhost:8000/docs
echo   Frontend : http://localhost:3000
echo  ==========================================
echo.
echo  (This window can be closed - services run in their own windows)
echo  (To stop everything run stop_neo4j.bat)
echo.
pause