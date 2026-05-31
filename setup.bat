@echo off
echo ================================
echo    ALOC Downloader Setup
echo ================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Downloading installer...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo Installing Python silently...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
    del python_installer.exe
    echo Python installed. Refreshing PATH...
    call refreshenv >nul 2>&1
) else (
    echo Python already installed.
    python --version
)

echo.
echo Installing required packages...
python -m pip install --upgrade pip -q
python -m pip install requests python-dotenv watchdog -q

echo.
echo All packages installed:
python -m pip show requests python-dotenv watchdog | findstr "Name Version"

echo.
echo Setup complete! You can now run:
echo   python download.py       ^(in one terminal^)
echo   python autopush.py       ^(in another terminal^)
echo.
pause
