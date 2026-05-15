[CmdletBinding()]
param(
    [string]$PythonVersion = "3.12",
    [switch]$SkipProjectSync,
    [switch]$SkipUvSelfUpdate
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Add-PathEntry {
    param([Parameter(Mandatory = $true)][string]$PathEntry)

    if (-not (Test-Path $PathEntry)) {
        return
    }

    $sessionEntries = @($env:Path -split ";") | Where-Object { $_ }
    if ($sessionEntries -notcontains $PathEntry) {
        $env:Path = ($sessionEntries + $PathEntry) -join ";"
    }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $userEntries = @($userPath -split ";") | Where-Object { $_ }
    if ($userEntries -notcontains $PathEntry) {
        $newUserPath = (($userEntries + $PathEntry) | Select-Object -Unique) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    }
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

function Test-UvToolInstalled {
    param([Parameter(Mandatory = $true)][string]$ToolName)

    $toolList = & uv tool list 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    return [bool]($toolList | Select-String -Pattern ("^{0}\s" -f [regex]::Escape($ToolName)))
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$uvBinDir = Join-Path $HOME ".local\bin"

Write-Step "Ensuring uv is available"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing with Astral's official installer..."
    Invoke-Expression (Invoke-RestMethod "https://astral.sh/uv/install.ps1")
}

Add-PathEntry -PathEntry $uvBinDir

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is still unavailable after installation. Restart the shell and rerun the script."
}

Write-Step "Updating uv"
if ($SkipUvSelfUpdate) {
    Write-Host "Skipping uv self update by request."
}
else {
    Invoke-Checked -FilePath "uv" -ArgumentList @("self", "update")
}

Write-Step "Ensuring Python $PythonVersion is installed via uv"
Invoke-Checked -FilePath "uv" -ArgumentList @("python", "install", $PythonVersion)

Write-Step "Ensuring uv tool bin directory is on PATH"
$toolBinDir = (& uv tool dir --bin).Trim()
if (-not $toolBinDir) {
    throw "Failed to resolve uv tool bin directory."
}
Add-PathEntry -PathEntry $toolBinDir

Write-Step "Ensuring global Astral tooling"
foreach ($toolName in @("ruff", "ty")) {
    if (Test-UvToolInstalled -ToolName $toolName) {
        Write-Host "$toolName already installed. Upgrading..."
        Invoke-Checked -FilePath "uv" -ArgumentList @("tool", "upgrade", "--python", $PythonVersion, $toolName)
    }
    else {
        Write-Host "$toolName not installed. Installing..."
        Invoke-Checked -FilePath "uv" -ArgumentList @("tool", "install", "--python", $PythonVersion, "$toolName@latest")
    }
}

if (-not $SkipProjectSync -and (Test-Path (Join-Path $repoRoot "pyproject.toml"))) {
    Write-Step "Syncing project-local dependencies"
    $dataDir = Join-Path $repoRoot "data"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir | Out-Null
    }
    Push-Location $repoRoot
    try {
        Invoke-Checked -FilePath "uv" -ArgumentList @("sync", "--all-groups", "--frozen", "--python", $PythonVersion, "--managed-python", "--link-mode", "copy")
    }
    finally {
        Pop-Location
    }
}
elseif ($SkipProjectSync) {
    Write-Step "Skipping project sync by request"
}
else {
    Write-Step "No pyproject.toml found; skipping project sync"
}

Write-Step "Verification summary"
Invoke-Checked -FilePath "uv" -ArgumentList @("--version")
Invoke-Checked -FilePath "uv" -ArgumentList @("python", "find", $PythonVersion)
Invoke-Checked -FilePath "uv" -ArgumentList @("tool", "run", "ruff", "--version")
Invoke-Checked -FilePath "uv" -ArgumentList @("tool", "run", "ty", "--version")
if (Test-Path (Join-Path $repoRoot "pyproject.toml")) {
    Push-Location $repoRoot
    try {
        Invoke-Checked -FilePath "uv" -ArgumentList @("run", "--python", $PythonVersion, "python", "-c", "import mlfq_os_simulator; print('Package import OK')")
        Invoke-Checked -FilePath "uv" -ArgumentList @("run", "--python", $PythonVersion, "python", "-c", "import filelock, pandas, plotly, pydantic, streamlit; print('Project dependencies OK')")
        if (Test-Path (Join-Path $repoRoot "app.py")) {
            Invoke-Checked -FilePath "uv" -ArgumentList @("run", "--python", $PythonVersion, "python", "-c", "import app; print('App import OK')")
        }
        Invoke-Checked -FilePath "uv" -ArgumentList @("run", "--group", "dev", "--python", $PythonVersion, "pytest", "--version")
        Invoke-Checked -FilePath "uv" -ArgumentList @("run", "--group", "dev", "--python", $PythonVersion, "ruff", "--version")
        Invoke-Checked -FilePath "uv" -ArgumentList @("run", "--group", "dev", "--python", $PythonVersion, "ty", "--version")
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Global tooling ready: uv, Python $PythonVersion, ruff, ty"
Write-Host "Project dependencies remain local and are managed with uv sync --frozen."
Write-Host "Next step: run .\\scripts\\run-project.ps1"
