# Script to permanently add Anaconda to PATH
# Run this script as Administrator for best results

$anacondaPaths = @(
    "$env:USERPROFILE\Anaconda3",
    "$env:USERPROFILE\Anaconda3\Scripts",
    "$env:USERPROFILE\Anaconda3\Library\bin"
)

# Get current user PATH
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")

# Check if Anaconda paths are already in PATH
$pathsToAdd = @()
foreach ($path in $anacondaPaths) {
    if ($currentPath -notlike "*$path*") {
        $pathsToAdd += $path
    }
}

if ($pathsToAdd.Count -gt 0) {
    # Add new paths to the beginning of PATH
    $newPath = ($pathsToAdd -join ";") + ";" + $currentPath
    
    # Set the new PATH for the user
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    
    Write-Host "Successfully added Anaconda to PATH!" -ForegroundColor Green
    Write-Host "Added paths:" -ForegroundColor Yellow
    $pathsToAdd | ForEach-Object { Write-Host "  $_" }
    Write-Host "`nPlease restart your terminal for changes to take effect." -ForegroundColor Cyan
} else {
    Write-Host "Anaconda paths are already in PATH." -ForegroundColor Yellow
}

# Display current Python configuration
Write-Host "`nCurrent Python configuration:" -ForegroundColor Cyan
& "$env:USERPROFILE\Anaconda3\python.exe" --version 