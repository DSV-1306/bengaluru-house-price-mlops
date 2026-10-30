# Saves the image currently on the clipboard (e.g. from Win+Shift+S) to docs/screenshots/<Name>.png
# Usage:  powershell -STA -File scripts\save-screenshot.ps1 phase1-model-comparison
param([Parameter(Mandatory = $true)][string]$Name)

Add-Type -AssemblyName System.Windows.Forms, System.Drawing

$outDir = Join-Path $PSScriptRoot "..\docs\screenshots"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outFile = Join-Path (Resolve-Path $outDir) ($Name -replace '\.png$', '')
$outFile = "$outFile.png"

$img = [System.Windows.Forms.Clipboard]::GetImage()
if ($null -eq $img) {
    Write-Host "No image on the clipboard. Press Win+Shift+S, drag over the area, then run this again." -ForegroundColor Yellow
    exit 1
}
$img.Save($outFile, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Host "Saved $outFile ($($img.Width)x$($img.Height))" -ForegroundColor Green
