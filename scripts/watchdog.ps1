# watchdog.ps1 — img-worker health + Claude CLI auth watchdog.
#
# Runs every 5 minutes (via Scheduled Task — see setup_keep_alive.ps1).
#
# Three checks in order:
#   1. docker compose ps img-worker is running. If not → docker compose up -d img-worker.
#   2. celery inspect ping succeeds against the img-worker. If 3 consecutive
#      misses, log a critical entry and (optionally) email via Postmark.
#   3. claude -p "ok" --output-format json inside the container returns a
#      valid response. If auth fails, log so the user can re-authenticate
#      Claude Code on the host.
#
# Logs to logs/watchdog.log relative to the project root.
# Stops on Ctrl-C interactively. As a Scheduled Task it runs once per fire.

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectRoot 'logs'
$LogFile = Join-Path $LogDir 'watchdog.log'
$StateFile = Join-Path $LogDir 'watchdog.state.json'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-Log([string]$Level, [string]$Message) {
    $line = "{0:yyyy-MM-ddTHH:mm:ssK}  [{1}]  {2}" -f (Get-Date), $Level, $Message
    Add-Content -Path $LogFile -Value $line
    if ($Level -in 'WARN', 'ERROR') { Write-Host $line }
}

function Get-State {
    if (Test-Path $StateFile) {
        try { return Get-Content $StateFile -Raw | ConvertFrom-Json -ErrorAction Stop } catch { }
    }
    return [pscustomobject]@{ celery_misses = 0; claude_misses = 0 }
}

function Save-State($state) {
    $state | ConvertTo-Json | Set-Content -Path $StateFile -Encoding UTF8
}

Push-Location $ProjectRoot
try {
    Write-Log INFO "watchdog tick"
    $state = Get-State

    # 1. Ensure img-worker is running.
    $running = $false
    try {
        $ps = & docker compose ps img-worker --format json 2>$null
        if ($LASTEXITCODE -eq 0 -and $ps) {
            $running = ($ps -match '"State"\s*:\s*"running"')
        }
    } catch {
        Write-Log WARN "docker compose ps failed: $($_.Exception.Message)"
    }
    if (-not $running) {
        Write-Log WARN "img-worker not running — starting"
        & docker compose up -d img-worker 2>&1 | Out-Null
        Start-Sleep -Seconds 10
    }

    # 2. Celery liveness.
    $celeryOk = $false
    try {
        $out = & docker compose exec -T api celery -A config inspect ping 2>$null
        $celeryOk = ($LASTEXITCODE -eq 0 -and $out -match 'pong')
    } catch { }
    if ($celeryOk) {
        if ($state.celery_misses -gt 0) { Write-Log INFO "celery recovered" }
        $state.celery_misses = 0
    } else {
        $state.celery_misses += 1
        Write-Log WARN "celery ping miss ($($state.celery_misses) consecutive)"
        if ($state.celery_misses -ge 3) {
            Write-Log ERROR "celery down for 3+ ticks — operator intervention may be needed"
        }
    }

    # 3. Claude CLI auth check (inside the container).
    $claudeOk = $false
    try {
        $out = & docker compose exec -T img-worker claude -p "ok" --output-format json 2>$null
        $claudeOk = ($LASTEXITCODE -eq 0 -and $out -and $out -notmatch 'auth' -and $out -notmatch 'login')
    } catch { }
    if ($claudeOk) {
        if ($state.claude_misses -gt 0) { Write-Log INFO "claude CLI recovered" }
        $state.claude_misses = 0
    } else {
        $state.claude_misses += 1
        Write-Log WARN "claude CLI miss ($($state.claude_misses) consecutive)"
        if ($state.claude_misses -ge 2) {
            Write-Log ERROR "claude CLI auth likely expired — run 'claude' on the host to re-authenticate"
        }
    }

    Save-State $state
    Write-Log INFO "tick done (celery_misses=$($state.celery_misses), claude_misses=$($state.claude_misses))"
} finally {
    Pop-Location
}
