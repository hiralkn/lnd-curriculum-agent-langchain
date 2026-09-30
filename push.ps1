# push.ps1
param (
    [string]$CommitMessage
)

# 1. Ensure we are in a Git repository
if (-not (Test-Path .git)) {
    Write-Error "Error: This directory is not a Git repository. Run 'git init' first."
    exit 1
}

# 2. Get or prompt for the commit message
if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
    $CommitMessage = Read-Host "Enter your commit message"
}

if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
    Write-Warning "Commit cancelled: A commit message is required."
    exit 1
}

# 3. Stage all local changes
Write-Host "Staging changes..." -ForegroundColor Cyan
git add .

# 4. Commit changes securely using standard arguments
Write-Host "Committing changes..." -ForegroundColor Cyan
git commit -m "$CommitMessage"

# 5. Determine current branch name dynamically
$Branch = git branch --show-current

# 6. Push to GitHub
Write-Host "Pushing to GitHub on branch '$Branch'..." -ForegroundColor Cyan
git push origin $Branch

Write-Host "Successfully uploaded to GitHub!" -ForegroundColor Green
