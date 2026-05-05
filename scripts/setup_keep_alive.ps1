# setup_keep_alive.ps1 — one-shot installer for the flyer-generator
# host-side keep-alive infrastructure. Idempotent.
#
# Creates / updates three Windows Scheduled Tasks (all run as the current
# user, at logon, with task scheduler retrying on failure) and applies the
# AC power policies that prevent the machine from sleeping while the
# prototype flyer-generator is in service.
#
# Tasks:
#   YakimaFlyer-PowerPolicy  — runs once at logon, applies powercfg overrides
#   YakimaFlyer-KeepAwake    — runs on a 1-minute trigger that never ends, runs
#                              scripts/keep_awake.ps1 in the background
#   YakimaFlyer-Watchdog     — runs every 5 minutes, runs scripts/watchdog.ps1
#
# Run in an elevated PowerShell session.
#
# Tear down with: scripts/setup_keep_alive.ps1 -Uninstall

[CmdletBinding()]
param([switch]$Uninstall)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptsDir = Join-Path $ProjectRoot 'scripts'
$KeepAwakeScript = Join-Path $ScriptsDir 'keep_awake.ps1'
$WatchdogScript = Join-Path $ScriptsDir 'watchdog.ps1'

# Resolve the PowerShell executable (prefer pwsh.exe; fall back to Windows PS).
$PSExe = (Get-Command pwsh.exe -ErrorAction SilentlyContinue)?.Source
if (-not $PSExe) { $PSExe = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source }
if (-not $PSExe) { throw "Could not locate pwsh.exe or powershell.exe on PATH." }

$TaskNames = @{
    Power     = 'YakimaFlyer-PowerPolicy'
    KeepAwake = 'YakimaFlyer-KeepAwake'
    Watchdog  = 'YakimaFlyer-Watchdog'
}

function Remove-IfExists([string]$Name) {
    $existing = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false
        Write-Host "Removed task: $Name"
    }
}

if ($Uninstall) {
    foreach ($n in $TaskNames.Values) { Remove-IfExists $n }
    Write-Host "Uninstall complete. Power-policy overrides remain in place; revert manually if you want sleep back:" -ForegroundColor Yellow
    Write-Host "  powercfg /change standby-timeout-ac 30"
    Write-Host "  powercfg /change hibernate-timeout-ac 60"
    return
}

if (-not (Test-Path $KeepAwakeScript)) { throw "Missing $KeepAwakeScript" }
if (-not (Test-Path $WatchdogScript))  { throw "Missing $WatchdogScript" }

Write-Host "Setting up flyer-generator keep-alive infrastructure..."
Write-Host "  Project: $ProjectRoot"
Write-Host "  PowerShell: $PSExe"

# 1. Power policy — never sleep / hibernate on AC. Re-applied at every logon
#    via the scheduled task so a fresh OS image / domain GPO can't override.
Write-Host "[1/3] Applying power policy..."
foreach ($pair in @(
    @{ Name = 'standby-timeout-ac';    Value = 0 }
    @{ Name = 'hibernate-timeout-ac';  Value = 0 }
)) {
    & powercfg /change $pair.Name $pair.Value
    Write-Host "       powercfg /change $($pair.Name) $($pair.Value)"
}

# Wrap the powercfg invocations in a Scheduled Task that re-applies them at logon.
$PowerCommand = "powercfg /change standby-timeout-ac 0; powercfg /change hibernate-timeout-ac 0"
$PowerAction = New-ScheduledTaskAction -Execute $PSExe -Argument "-NoProfile -WindowStyle Hidden -Command `"$PowerCommand`""
$PowerTrigger = New-ScheduledTaskTrigger -AtLogOn
$PowerSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Remove-IfExists $TaskNames.Power
Register-ScheduledTask -TaskName $TaskNames.Power `
    -Action $PowerAction -Trigger $PowerTrigger -Settings $PowerSettings `
    -Description "Re-apply 'never sleep' AC power policy at logon for flyer-generator." | Out-Null
Write-Host "       task registered: $($TaskNames.Power)"

# 2. Keep-awake heartbeat.
Write-Host "[2/3] Registering keep-awake heartbeat..."
$KeepAction = New-ScheduledTaskAction -Execute $PSExe -Argument "-NoProfile -WindowStyle Hidden -File `"$KeepAwakeScript`""
$KeepTrigger = New-ScheduledTaskTrigger -AtLogOn
$KeepSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartInterval (New-TimeSpan -Minutes 1) -RestartCount 3

Remove-IfExists $TaskNames.KeepAwake
Register-ScheduledTask -TaskName $TaskNames.KeepAwake `
    -Action $KeepAction -Trigger $KeepTrigger -Settings $KeepSettings `
    -Description "Mouse-jiggler heartbeat — keeps the host awake while the flyer-generator is in service." | Out-Null
Write-Host "       task registered: $($TaskNames.KeepAwake)"

# 3. Watchdog every 5 minutes.
Write-Host "[3/3] Registering container watchdog..."
$WatchAction = New-ScheduledTaskAction -Execute $PSExe -Argument "-NoProfile -WindowStyle Hidden -File `"$WatchdogScript`""
$WatchTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ([TimeSpan]::MaxValue)
$WatchSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Remove-IfExists $TaskNames.Watchdog
Register-ScheduledTask -TaskName $TaskNames.Watchdog `
    -Action $WatchAction -Trigger $WatchTrigger -Settings $WatchSettings `
    -Description "Watchdog — restarts img-worker if down, surfaces Claude CLI auth failures." | Out-Null
Write-Host "       task registered: $($TaskNames.Watchdog)"

Write-Host "`nKeep-alive setup complete." -ForegroundColor Green
Write-Host "Logs land in:"
Write-Host "  $ProjectRoot\logs\keep_awake.log"
Write-Host "  $ProjectRoot\logs\watchdog.log"
Write-Host ""
Write-Host "If Claude CLI auth ever expires, run 'claude' interactively on the host to re-authenticate."
Write-Host "To uninstall: pwsh scripts/setup_keep_alive.ps1 -Uninstall"
