@echo off
title DOM Taxonomy Browser
echo.
echo  =============================================
echo   DOM Taxonomy Browser — STRADA
echo  =============================================
echo.

:: Detect Python
set PY=
where python  >nul 2>&1 && set PY=python
if "%PY%"=="" where python3 >nul 2>&1 && set PY=python3
if "%PY%"=="" where py     >nul 2>&1 && set PY=py
if "%PY%"=="" (
    echo  ERROR: Python not found.
    echo  Please install Python from https://www.python.org
    echo.
    pause
    exit /b 1
)

echo  Python found: %PY%
echo  Starting local server on http://localhost:8080 ...
echo.

:: Open browser after 1s delay (in background)
start "" /B cmd /C "timeout /t 1 /nobreak >nul && start http://localhost:8080"

:: Run server in foreground (Ctrl+C to stop)
%PY% -m http.server 8080

echo.
echo  Server stopped.
pause
