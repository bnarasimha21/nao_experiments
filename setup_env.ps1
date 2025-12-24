# Setup script for PyNAOqi environment on Windows
# Run with: .\setup_env.ps1
# Or: powershell -ExecutionPolicy Bypass -File .\setup_env.ps1

# Default SDK path - Auto-detected
$SDK_PATH = "C:\naoqi\pynaoqi-python2.7-2.8.6.23-win64-vs2015-20191127_152649"

# Check if SDK path exists
if (-not (Test-Path $SDK_PATH)) {
    Write-Host "⚠️  WARNING: SDK path not found: $SDK_PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please update the SDK_PATH variable in this script with the actual path to your PyNAOqi SDK." -ForegroundColor Yellow
    Write-Host "Download from: https://www.aldebaran.com/en/support" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Expected SDK name: pynaoqi-python2.7-2.8.6.23-win32-vs2015" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Check if Python 2.7 is installed
$python27Path = "C:\Python27\python.exe"
$python27InPath = $false

# Check if Python 2.7 is at default location
if (Test-Path $python27Path) {
    $pythonVersion = & $python27Path --version 2>&1
    Write-Host "✅ Found Python 2.7 at: C:\Python27" -ForegroundColor Green
    Write-Host "   Version: $pythonVersion" -ForegroundColor Gray
    
    # Add Python 2.7 to PATH for this session if not already there
    if ($env:PATH -notlike "*Python27*") {
        $env:PATH = "C:\Python27;C:\Python27\Scripts;$env:PATH"
        Write-Host "   Added Python 2.7 to PATH for this session" -ForegroundColor Gray
    }
    $python27InPath = $true
} else {
    # Check if python in PATH is 2.7
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "2\.7") {
            Write-Host "✅ Python 2.7 found in PATH" -ForegroundColor Green
            Write-Host "   Version: $pythonVersion" -ForegroundColor Gray
            $python27InPath = $true
        } else {
            Write-Host "⚠️  WARNING: Python 2.7 is required, but found: $pythonVersion" -ForegroundColor Yellow
            Write-Host "Please install Python 2.7 from: https://www.python.org/downloads/release/python-2718/" -ForegroundColor Yellow
            Write-Host "Install to: C:\Python27" -ForegroundColor Yellow
            Write-Host ""
        }
    } else {
        Write-Host "⚠️  WARNING: Python 2.7 not found" -ForegroundColor Yellow
        Write-Host "Please install Python 2.7 from: https://www.python.org/downloads/release/python-2718/" -ForegroundColor Yellow
        Write-Host "Install to: C:\Python27" -ForegroundColor Yellow
        Write-Host ""
    }
}

# Set environment variables for current session
# Note: naoqi module is in lib folder, not site-packages
$env:PYTHONPATH = "$SDK_PATH\lib"
$env:PATH = "$SDK_PATH\lib;$env:PATH"

Write-Host "✅ PyNAOqi environment configured for this session!" -ForegroundColor Green
Write-Host ""
Write-Host "Environment variables set:" -ForegroundColor Cyan
Write-Host "  PYTHONPATH = $env:PYTHONPATH" -ForegroundColor Cyan
Write-Host "  PATH updated with: $SDK_PATH\lib" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test with:" -ForegroundColor Yellow
Write-Host "  python test_setup.py" -ForegroundColor White
Write-Host ""
Write-Host "Run examples:" -ForegroundColor Yellow
Write-Host "  python examples\say_hello.py <robot_ip>" -ForegroundColor White
Write-Host "  python examples\wave.py <robot_ip>" -ForegroundColor White
Write-Host "  python examples\dance.py <robot_ip>" -ForegroundColor White
Write-Host ""
Write-Host "Note: These environment variables are only set for this PowerShell session." -ForegroundColor Gray
Write-Host "To make them permanent, use the System Environment Variables settings." -ForegroundColor Gray

