# Remove the dependencies and generated artifacts installed by install.*.
# Interactive menu; several items can be selected at once.
# No git command is used, and protected paths are never touched.

$scriptDir = Split-Path -Parent $PSScriptRoot
$projectRoot = $scriptDir
while (-not (Test-Path -LiteralPath (Join-Path $projectRoot "apps"))) {
    $parent = Split-Path -Parent $projectRoot
    if ($parent -eq $projectRoot) {
        break
    }
    $projectRoot = $parent
}

function Remove-Path {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        Write-Host "Removing $Path"
        Remove-Item -Recurse -Force -LiteralPath $Path
    }
}

function Remove-App {
    param([string]$App)
    $dir = Join-Path (Join-Path $projectRoot "apps") $App
    if (-not (Test-Path -LiteralPath $dir)) {
        Write-Host "$App not found, skipping"
        return
    }
    Write-Host "Removing dependencies of $App..."
    Remove-Path (Join-Path $dir ".venv")
    Remove-Path (Join-Path $dir ".pytest_cache")
    Remove-Path (Join-Path $dir ".coverage")
    Remove-Path (Join-Path $dir "htmlcov")
    Remove-Path (Join-Path $dir "coverage.xml")
    Remove-Path (Join-Path $dir "coverage.txt")
    Remove-Path (Join-Path $dir "node_modules")
    Remove-Path (Join-Path $dir "test-results")
    Remove-Path (Join-Path $dir "playwright-report")
    Remove-Path (Join-Path $dir "uv.lock")
    Remove-Path (Join-Path $dir "poetry.lock")
    $cache = Get-ChildItem -LiteralPath $dir -Directory -Filter "__pycache__" -Recurse
    foreach ($folder in $cache) {
        Remove-Path $folder.FullName
    }
}

function Remove-Root {
    Write-Host "Removing dependencies of the root project..."
    Remove-Path (Join-Path $projectRoot ".venv")
    Remove-Path (Join-Path $projectRoot ".pytest_cache")
    Remove-Path (Join-Path $projectRoot ".coverage")
}

function Remove-GlobalTool {
    param([string]$Tool)
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv tool uninstall $Tool
        if ($LASTEXITCODE -ne 0) {
            throw "uv tool uninstall $Tool failed"
        }
    }
}

function Test-AppInstalled {
    param([string]$App)
    $dir = Join-Path (Join-Path $projectRoot "apps") $App
    if (-not (Test-Path -LiteralPath $dir)) { return $false }
    if (Test-Path -LiteralPath (Join-Path $dir ".venv")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir ".pytest_cache")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "node_modules")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "htmlcov")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "test-results")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "playwright-report")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir ".coverage")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "coverage.xml")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "coverage.txt")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "uv.lock")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "poetry.lock")) { return $true }
    $cache = Get-ChildItem -LiteralPath $dir -Directory -Filter "__pycache__" -Recurse -ErrorAction SilentlyContinue
    if ($cache) { return $true }
    return $false
}

function Test-RootInstalled {
    $dir = $projectRoot
    if (Test-Path -LiteralPath (Join-Path $dir ".venv")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir ".pytest_cache")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir ".coverage")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "uv.lock")) { return $true }
    if (Test-Path -LiteralPath (Join-Path $dir "poetry.lock")) { return $true }
    $cache = Get-ChildItem -LiteralPath $dir -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
    if ($cache) { return $true }
    return $false
}

function Test-GlobalToolInstalled {
    param([string]$Tool)
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $list = (uv tool list 2>$null) -join [Environment]::NewLine
        if ($list -match $Tool) { return $true }
    }
    return $false
}

function Select-Items {
    param([string[]]$Items)
    while ($true) {
        Write-Host ""
        Write-Host "Uninstallable items:"
        for ($i = 0; $i -lt $Items.Count; $i++) {
            Write-Host ("  {0}) {1}" -f ($i + 1), $Items[$i])
        }
        $choice = Read-Host "Select one or more [e.g. 1,3 5] (Enter to cancel)"
        if ([string]::IsNullOrWhiteSpace($choice)) {
            return @()
        }
        $choice = $choice.Trim()
        $selected = @()
        $invalid = $false
        foreach ($token in ($choice -split "[ ,]+")) {
            if ($token -notmatch "^[0-9]+$") {
                $invalid = $true
                continue
            }
            $index = [int]$token
            if ($index -lt 1 -or $index -gt $Items.Count) {
                $invalid = $true
                continue
            }
            $selected += $Items[$index - 1]
        }
        if (-not $invalid) {
            return $selected
        }
        Write-Host "Invalid selection, try again."
    }
}

$apps = Get-ChildItem -LiteralPath (Join-Path $projectRoot "apps") -Directory |
    Where-Object { (Test-Path (Join-Path $_.FullName "pyproject.toml")) -or (Test-Path (Join-Path $_.FullName "package.json")) } |
    ForEach-Object { $_.Name }
$items = @()
foreach ($app in $apps) {
    if (Test-AppInstalled $app) {
        $items += $app
    }
}
if (Test-RootInstalled) { $items += "root" }
if (Test-GlobalToolInstalled "graphify") { $items += "graphify" }
if (Test-GlobalToolInstalled "crawlee") { $items += "crawlee" }
if ($items.Count -eq 0) {
    Write-Host "Nothing to uninstall (no dependencies found)."
    return
}
$selected = Select-Items -Items $items
if ($selected.Count -eq 0) {
    Write-Host "Nothing selected, nothing removed."
} else {
    foreach ($item in $selected) {
        Write-Host "Removing dependencies of $item..."
        switch ($item) {
            "root" { Remove-Root }
            "graphify" { Remove-GlobalTool graphify }
            "crawlee" { Remove-GlobalTool crawlee }
            default { Remove-App $item }
        }
    }
    Write-Host "Done."
}