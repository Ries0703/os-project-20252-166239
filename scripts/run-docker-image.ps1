[CmdletBinding()]
param(
    [string]$ImageTag = "mlfq-os-simulator:local",
    [string]$ContainerName = "mlfq-os-simulator-local",
    [int]$Port = 8501,
    [string]$HostDataDir = "",
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$ArgumentList = @()
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        $joinedArgs = $ArgumentList -join " "
        throw "Command failed: $FilePath $joinedArgs"
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Không tìm thấy docker. Hãy cài Docker Desktop và đảm bảo daemon đang chạy."
}

if ($Rebuild) {
    Write-Step "Rebuilding image before run"
    Invoke-Checked -FilePath "powershell" -ArgumentList @(
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        (Join-Path $PSScriptRoot "build-docker-image.ps1"),
        "-ImageTag",
        $ImageTag
    )
}
else {
    Write-Step "Checking Docker image"
    & docker image inspect $ImageTag | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Không tìm thấy image '$ImageTag'. Hãy chạy .\\scripts\\build-docker-image.ps1 trước hoặc dùng -Rebuild."
    }
}

Write-Step "Removing old container if it exists"
& docker rm -f $ContainerName | Out-Null

$runArgs = @(
    "run",
    "-d",
    "--rm",
    "--name",
    $ContainerName,
    "-p",
    "${Port}:8501"
)

if ($HostDataDir) {
    $resolvedDataDir = Resolve-Path -Path $HostDataDir -ErrorAction SilentlyContinue
    if (-not $resolvedDataDir) {
        New-Item -ItemType Directory -Path $HostDataDir -Force | Out-Null
        $resolvedDataDir = Resolve-Path -Path $HostDataDir
    }
    $runArgs += @(
        "-v",
        "$($resolvedDataDir.Path):/app/data"
    )
}

$runArgs += $ImageTag

Write-Step "Starting container"
Invoke-Checked -FilePath "docker" -ArgumentList $runArgs

Write-Host ""
Write-Host "Container is running: $ContainerName" -ForegroundColor Green
Write-Host "Open in browser: http://localhost:$Port"
Write-Host "Stop container: docker rm -f $ContainerName"
