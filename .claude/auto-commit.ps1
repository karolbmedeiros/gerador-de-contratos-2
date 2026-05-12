$projectPath = "C:\Users\anabm\OneDrive\Documentos\aprendendo_claude"
Set-Location $projectPath

git add -A | Out-Null
git diff --staged --quiet 2>$null
$hasChanges = ($LASTEXITCODE -ne 0)

Add-Type -AssemblyName System.Windows.Forms
$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Application
$balloon.Visible = $true

if ($hasChanges) {
    $timestamp = Get-Date -Format "dd/MM HH:mm"
    git commit -m "chore: auto-save $timestamp" | Out-Null
    git push 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $balloon.BalloonTipTitle = "Git Auto-Save"
        $balloon.BalloonTipText = "Commit e push feitos! ($timestamp)"
    } else {
        $balloon.BalloonTipTitle = "Git Auto-Save - Erro"
        $balloon.BalloonTipText = "Push falhou. Verifique a conexao."
    }
} else {
    $balloon.BalloonTipTitle = "Git Auto-Save"
    $balloon.BalloonTipText = "Nenhuma alteracao para commitar."
}

$balloon.ShowBalloonTip(4000)
Start-Sleep -Seconds 4
$balloon.Dispose()
