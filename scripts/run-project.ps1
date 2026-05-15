[CmdletBinding()]
param(
    [string]$PythonVersion = "3.12",
    [int]$Port = 8501,
    [string]$DataDir = "",
    [switch]$SkipSync
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

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "Không tìm thấy uv. Hãy chạy .\\scripts\\setup-python-tooling.ps1 trước."
}

if (-not (Test-Path (Join-Path $repoRoot "pyproject.toml"))) {
    throw "Không tìm thấy pyproject.toml trong repo root."
}

if (-not (Test-Path (Join-Path $repoRoot "app.py"))) {
    throw "Không tìm thấy app.py trong repo root."
}

Push-Location $repoRoot
try {
    if (-not $SkipSync) {
        Write-Step "Syncing project environment"
        Invoke-Checked -FilePath "uv" -ArgumentList @(
            "sync",
            "--all-groups",
            "--frozen",
            "--python",
            $PythonVersion,
            "--managed-python",
            "--link-mode",
            "copy"
        )
    }

    if ($DataDir) {
        $env:MLFQ_DATA_DIR = $DataDir
        Write-Step "Using custom data directory: $DataDir"
    }

    $appUrl = "http://localhost:$Port"
    Write-Step "Starting Streamlit app"
    Write-Host "Open in browser: $appUrl"

    Invoke-Checked -FilePath "uv" -ArgumentList @(
        "run",
        "--python",
        $PythonVersion,
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        "$Port"
    )
}
finally {
    Pop-Location
}
