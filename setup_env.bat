@echo off
REM Setup script for PyNAOqi environment on Windows
REM Run with: setup_env.bat

REM Default SDK path - Auto-detected
set SDK_PATH=C:\naoqi\pynaoqi-python2.7-2.8.6.23-win64-vs2015-20191127_152649

REM Check if SDK path exists
if not exist "%SDK_PATH%" (
    echo ⚠️  WARNING: SDK path not found: %SDK_PATH%
    echo.
    echo Please update the SDK_PATH variable in this script with the actual path to your PyNAOqi SDK.
    echo Download from: https://www.aldebaran.com/en/support
    echo.
    echo Expected SDK name: pynaoqi-python2.7-2.8.6.23-win32-vs2015
    echo.
    pause
    exit /b 1
)

REM Check if Python 2.7 is installed
if exist "C:\Python27\python.exe" (
    echo ✅ Found Python 2.7 at: C:\Python27
    C:\Python27\python.exe --version
    echo    Added Python 2.7 to PATH for this session
    set PATH=C:\Python27;C:\Python27\Scripts;%PATH%
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  WARNING: Python 2.7 not found
        echo Please install Python 2.7 from: https://www.python.org/downloads/release/python-2718/
        echo Install to: C:\Python27
        echo.
    ) else (
        python --version 2>&1 | findstr /C:"2.7" >nul
        if errorlevel 1 (
            echo ⚠️  WARNING: Python 2.7 is required
            echo Please install Python 2.7 from: https://www.python.org/downloads/release/python-2718/
            echo Install to: C:\Python27
            echo.
        ) else (
            echo ✅ Python 2.7 found in PATH
            python --version
        )
    )
)

REM Set environment variables for current session
REM Note: naoqi module is in lib folder, not site-packages
set PYTHONPATH=%SDK_PATH%\lib
set PATH=%SDK_PATH%\lib;%PATH%

echo ✅ PyNAOqi environment configured for this session!
echo.
echo Environment variables set:
echo   PYTHONPATH = %PYTHONPATH%
echo   PATH updated with: %SDK_PATH%\lib
echo.
echo Test with:
echo   python test_setup.py
echo.
echo Run examples:
echo   python examples\say_hello.py ^<robot_ip^>
echo   python examples\wave.py ^<robot_ip^>
echo   python examples\dance.py ^<robot_ip^>
echo.
echo Note: These environment variables are only set for this Command Prompt session.
echo To make them permanent, use the System Environment Variables settings.
echo.

