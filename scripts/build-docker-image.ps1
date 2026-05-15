[CmdletBinding()]
param(
    [string]$ImageTag = "mlfq-os-simulator:local"
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

Push-Location $repoRoot
try {
    Write-Step "Building Docker image: $ImageTag"
    Invoke-Checked -FilePath "docker" -ArgumentList @(
        "build",
        "-t",
        $ImageTag,
        "."
    )
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Docker image ready: $ImageTag" -ForegroundColor Green
Write-Host "Next step: run .\\scripts\\run-docker-image.ps1 -ImageTag `"$ImageTag`""
