# Pulls fresh data from the Pi, rebuilds the report page, and publishes it.
#   .\update.ps1            pull, rebuild, commit and push
#   .\update.ps1 -NoPush    pull and rebuild only (preview docs\index.html locally)
param([switch]$NoPush)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

& "$PSScriptRoot\scripts\pull-kuma.ps1"
python analyze.py
if ($LASTEXITCODE -ne 0) { throw 'analyze.py failed' }
python build_site.py
if ($LASTEXITCODE -ne 0) { throw 'build_site.py failed' }

if ($NoPush) { Write-Host 'Rebuilt docs\index.html (not pushed).'; return }
git add docs
git commit -m "Update report $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git push
Write-Host 'Published. GitHub Pages usually refreshes within a minute or two.'
