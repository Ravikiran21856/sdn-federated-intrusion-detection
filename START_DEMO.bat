@echo off
TITLE AEGISNET - Zero-Day Federated IDS Project Demo
COLOR 0B
cls
echo ===============================================================================
echo      AEGISNET: Zero-Day Federated Intrusion Detection Matrix (CORE v2.4)
echo               College Demonstration and Project Defense Launcher
echo ===============================================================================
echo.
echo [*] Checking Python Installation...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your PATH!
    echo Please install Python 3.9+ and make sure 'Add to PATH' is checked.
    pause
    exit /b
)

echo [*] Launching 1-Click Interactive Defense Console...
python run_demo.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to run demo. Please check your dependencies.
    pause
)
