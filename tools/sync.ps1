# Pull the latest commits from .sync\poc.bundle into this repo.
# Run from the repo root:  powershell -ExecutionPolicy Bypass -File tools\sync.ps1
$ErrorActionPreference = "Stop"
$bundle = ".sync\poc.bundle"
if (-not (Test-Path $bundle)) { throw "No $bundle found. Nothing to sync." }
git bundle verify $bundle | Out-Null
if (-not (Test-Path ".git")) {
    git init -b main
    git fetch $bundle main
    git reset --hard FETCH_HEAD
} else {
    git pull --ff-only $bundle main
}
git log --oneline -5
