# Copies Uptime Kuma's database off the Pi into data\ without changing anything on the Pi.
# The Pi address and SSH username come from local.config.json (see local.config.example.json).
param([string]$PiHost, [string]$User)

$root = Split-Path $PSScriptRoot -Parent
$configPath = Join-Path $root 'local.config.json'
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    if (-not $PiHost) { $PiHost = $config.PiHost }
    if (-not $User) { $User = $config.User }
}
if (-not $PiHost) { $PiHost = Read-Host 'Raspberry Pi address' }
if (-not $User) { $User = Read-Host 'Raspberry Pi SSH username' }

$data = Join-Path $root 'data'
New-Item -ItemType Directory -Force $data | Out-Null
$tar = Join-Path $data 'kuma.tar'

Write-Host "Connecting to $User@$PiHost (enter the Pi password when asked)..."
cmd /c "ssh -o StrictHostKeyChecking=accept-new $User@$PiHost sh -s < `"$PSScriptRoot\remote.sh`" > `"$tar`""
if ($LASTEXITCODE -ne 0) { throw "ssh failed with exit code $LASTEXITCODE" }

$db = Join-Path $data 'db'
if (Test-Path $db) { Remove-Item -Recurse -Force $db }
New-Item -ItemType Directory -Force $db | Out-Null
tar -xf $tar -C $db
Write-Host "Database copied to $db"
