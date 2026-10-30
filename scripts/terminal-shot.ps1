# Runs a command and saves its real output as a terminal-style PNG in docs/screenshots/.
# Usage:  powershell -File scripts\terminal-shot.ps1 phase4-docker-images "docker images --filter reference=house-price-*"
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Command
)
Add-Type -AssemblyName System.Drawing
[Console]::OutputEncoding = [Text.Encoding]::UTF8   # so native tools' UTF-8 output (e.g. the ₹ sign) is read correctly

$output = (Invoke-Expression "$Command 2>&1" | Out-String -Width 160).TrimEnd() -split "`r?`n"
$lines = @("PS $((Get-Location).Path)> $Command") + $output

$font = New-Object System.Drawing.Font("Consolas", 13)
$probe = [System.Drawing.Graphics]::FromImage((New-Object System.Drawing.Bitmap 1, 1))
$charW = $probe.MeasureString("M" * 100, $font).Width / 100
$lineH = [int][Math]::Ceiling($font.GetHeight($probe)) + 2
$maxLen = ($lines | Measure-Object -Property Length -Maximum).Maximum
$width = [int][Math]::Max(900, [Math]::Ceiling($maxLen * $charW) + 40)
$height = $lines.Count * $lineH + 40

$bmp = New-Object System.Drawing.Bitmap $width, $height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
$g.Clear([System.Drawing.Color]::FromArgb(12, 12, 12))
$prompt = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(249, 241, 165))
$text = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(204, 204, 204))
$y = 20
for ($i = 0; $i -lt $lines.Count; $i++) {
    $g.DrawString($lines[$i], $font, $(if ($i -eq 0) { $prompt } else { $text }), 20, $y)
    $y += $lineH
}
$outDir = Join-Path $PSScriptRoot "..\docs\screenshots"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out = Join-Path (Resolve-Path $outDir) "$Name.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "Saved $out ($width x $height)"
