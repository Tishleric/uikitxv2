# Script to remove direct Python installation and clean up
# This script guides you through the process

Write-Host "=== Python Installation Cleanup Guide ===" -ForegroundColor Cyan
Write-Host "This script will help you remove the direct Python installation." -ForegroundColor Yellow
Write-Host ""

# Check for the direct Python installation
$pythonPath = "$env:LOCALAPPDATA\Programs\Python\Python313"
if (Test-Path $pythonPath) {
    Write-Host "Found direct Python installation at:" -ForegroundColor Green
    Write-Host "  $pythonPath" -ForegroundColor White
    Write-Host ""
    
    # Option 1: Use Windows uninstaller
    Write-Host "Option 1: Use Windows Uninstaller (Recommended)" -ForegroundColor Yellow
    Write-Host "1. Open Windows Settings (Win + I)"
    Write-Host "2. Go to Apps > Apps & features"
    Write-Host "3. Search for 'Python 3.13'"
    Write-Host "4. Click on it and select 'Uninstall'"
    Write-Host ""
    
    # Option 2: Manual removal
    Write-Host "Option 2: Manual Removal (if uninstaller not available)" -ForegroundColor Yellow
    $confirm = Read-Host "Do you want to manually remove Python 3.13? (yes/no)"
    
    if ($confirm -eq "yes") {
        Write-Host "Removing Python directory..." -ForegroundColor Yellow
        try {
            Remove-Item -Path $pythonPath -Recurse -Force
            Write-Host "Successfully removed Python directory!" -ForegroundColor Green
        } catch {
            Write-Host "Error removing directory. You may need to run as Administrator." -ForegroundColor Red
            Write-Host "Error: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Direct Python installation not found at expected location." -ForegroundColor Yellow
}

# Clean up Windows Store Python alias
Write-Host "`nChecking Windows Store Python aliases..." -ForegroundColor Cyan
Write-Host "To disable Windows Store Python aliases:" -ForegroundColor Yellow
Write-Host "1. Open Windows Settings"
Write-Host "2. Go to Apps > Advanced app settings > App execution aliases"
Write-Host "3. Turn OFF both 'python.exe' and 'python3.exe' aliases"
Write-Host ""

# Verify Anaconda is working
Write-Host "Verifying Anaconda installation..." -ForegroundColor Cyan
$anacondaPython = "$env:USERPROFILE\Anaconda3\python.exe"
if (Test-Path $anacondaPython) {
    $version = & $anacondaPython --version 2>&1
    Write-Host "Anaconda Python found: $version" -ForegroundColor Green
    
    # Show conda info
    $condaExe = "$env:USERPROFILE\Anaconda3\Scripts\conda.exe"
    if (Test-Path $condaExe) {
        $condaVersion = & $condaExe --version 2>&1
        Write-Host "Conda version: $condaVersion" -ForegroundColor Green
    }
} else {
    Write-Host "Anaconda Python not found!" -ForegroundColor Red
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Restart your terminal/PowerShell" -ForegroundColor Yellow
Write-Host "2. Verify Python works: python --version" -ForegroundColor Yellow
Write-Host "3. Verify pip works: pip --version" -ForegroundColor Yellow
Write-Host "4. Verify conda works: conda --version" -ForegroundColor Yellow
Write-Host ""
Write-Host "If you encounter issues after restart, run:" -ForegroundColor White
Write-Host "  conda init powershell" -ForegroundColor Green 