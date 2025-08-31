param(
    [Parameter(Mandatory=$true, Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$InputFiles,

    [string]$Suffix = '_sorted_by_abs_moneyness'
)

function Get-OutputPath {
    param(
        [string]$InputPath,
        [string]$Suffix
    )
    $dir  = [System.IO.Path]::GetDirectoryName($InputPath)
    $name = [System.IO.Path]::GetFileNameWithoutExtension($InputPath)
    $ext  = [System.IO.Path]::GetExtension($InputPath)
    return [System.IO.Path]::Combine($dir, ($name + $Suffix + $ext))
}

foreach ($path in $InputFiles) {
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Error "File not found: $path"
        continue
    }

    $data = Import-Csv -LiteralPath $path
    if (-not $data) {
        Write-Warning "Empty or unreadable CSV: $path"
        continue
    }

    # Ensure moneyness column exists
    $hasMoneyness = $false
    foreach ($h in $data[0].psobject.Properties.Name) {
        if ($h -eq 'moneyness') { $hasMoneyness = $true; break }
    }
    if (-not $hasMoneyness) {
        Write-Error "Column 'moneyness' not found in: $path"
        continue
    }

    # Create helper column for absolute moneyness (non-numeric -> NaN -> sort last)
    $withAbs = $data | ForEach-Object {
        $val = $_.moneyness
        $num = $null
        if ($null -ne $val -and "$val" -ne '') {
            # Try parse as double; if fails, keep $num as $null
            [double]$parsed = $null
            if ([double]::TryParse("$val", [ref]$parsed)) { $num = [math]::Abs($parsed) }
        }
        $_ | Add-Member -NotePropertyName abs_moneyness -NotePropertyValue $num -Force
        $_
    }

    $sorted = $withAbs | Sort-Object -Property @{Expression='abs_moneyness';Descending=$true}, @{Expression='moneyness';Descending=$true}
    $sorted = $sorted | Select-Object -Property * -ExcludeProperty abs_moneyness

    $outPath = Get-OutputPath -InputPath $path -Suffix $Suffix
    $sorted | Export-Csv -NoTypeInformation -LiteralPath $outPath
    Write-Output "Wrote: $outPath"
}


