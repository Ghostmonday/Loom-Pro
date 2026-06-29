# MiniMax Windows sandbox — post-install integration (run as Administrator)
#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

Write-Host "==> MiniMax Windows sandbox post-install" -ForegroundColor Cyan

function Find-ShareRoot {
    param([string]$Tag = "hostshare")
    $candidates = @(
        "Z:\",
        "Y:\",
        "X:\"
    )
    foreach ($drive in $candidates) {
        if (Test-Path (Join-Path $drive "windows-postinstall.ps1")) {
            return $drive
        }
    }
    $shares = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.DisplayRoot -like "*$Tag*" }
    if ($shares) {
        return ($shares[0].Root)
    }
    throw "hostshare not mounted. Map virtio-9p share first (see README.txt on Linux host)."
}

$ShareRoot = Find-ShareRoot
Write-Host "    Share: $ShareRoot"

# Node.js LTS (required for mmx-cli)
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "==> Installing Node.js LTS..."
    $nodeMsi = "$env:TEMP\node-lts.msi"
    Invoke-WebRequest -Uri "https://nodejs.org/dist/v22.16.0/node-v22.16.0-x64.msi" -OutFile $nodeMsi
    Start-Process msiexec.exe -ArgumentList "/i `"$nodeMsi`" /qn" -Wait
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

Write-Host "    Node: $(node -v)  npm: $(npm -v)"

# mmx-cli
if (-not (Get-Command mmx -ErrorAction SilentlyContinue)) {
    Write-Host "==> Installing mmx-cli..."
    npm install -g mmx-cli
}

$mmxConfigSrc = Join-Path $ShareRoot "mmx-config.json"
$mmxDir = Join-Path $env:USERPROFILE ".mmx"
New-Item -ItemType Directory -Force -Path $mmxDir | Out-Null
if (Test-Path $mmxConfigSrc) {
    Copy-Item $mmxConfigSrc (Join-Path $mmxDir "config.json") -Force
    Write-Host "==> mmx config copied from host share"
} else {
    Write-Host "WARN: no mmx-config.json on share — run: mmx auth login --api-key sk-..." -ForegroundColor Yellow
}

mmx auth status

# Hermes Agent (native Windows)
$hermesHome = Join-Path $env:LOCALAPPDATA "hermes"
if (-not (Test-Path (Join-Path $hermesHome "hermes-agent"))) {
    Write-Host "==> Installing Hermes Agent (native Windows)..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    & ([scriptblock]::Create((Invoke-RestMethod "https://hermes-agent.nousresearch.com/install.ps1"))) -SkipSetup
}

$hermesBin = Join-Path $hermesHome "bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$hermesBin*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$hermesBin", "User")
    $env:Path += ";$hermesBin"
}

# MiniMax provider env for Hermes
$hermesEnv = Join-Path $hermesHome ".env"
if (Test-Path (Join-Path $mmxDir "config.json")) {
    $cfg = Get-Content (Join-Path $mmxDir "config.json") | ConvertFrom-Json
    if ($cfg.apiKey) {
        $line = "MINIMAX_API_KEY=$($cfg.apiKey)"
        if (Test-Path $hermesEnv) {
            $content = Get-Content $hermesEnv -Raw
            if ($content -notmatch "MINIMAX_API_KEY=") {
                Add-Content $hermesEnv $line
            }
        } else {
            Set-Content $hermesEnv $line
        }
        Write-Host "==> MINIMAX_API_KEY written to Hermes .env"
    }
}

Write-Host ""
Write-Host "==> Ready. Test commands (new terminal after PATH refresh):" -ForegroundColor Green
Write-Host "    mmx text chat --message `"Hello from Windows`" --output json --quiet"
Write-Host "    hermes -p minimax-boss -m MiniMax-M3 --provider minimax --yolo -z `"ping`""
Write-Host ""
Write-Host "Gaijinn executor profile on share: project.executor-profile.json" -ForegroundColor DarkGray