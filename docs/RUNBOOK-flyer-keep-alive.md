# Flyer-generator keep-alive runbook

Operator guide for the prototype flyer-generator's host-side infrastructure.
**Prototype-only**. When the AI backend swaps to Gemini (`FLYER_BACKEND=gemini`),
nothing in this document is needed; tear down with `setup_keep_alive.ps1 -Uninstall`.

## What this is for

The prototype flyer-generator backend (`apps/tools/services/flyer_generator/backends/claude_cli.py`)
shells out to the local `claude` CLI inside the `img-worker` container, which
mounts the host's `~/.claude` OAuth credentials. Three host-side concerns
need ongoing care:

1. **Machine awake**. If the host sleeps, the img-worker can't service
   incoming flyer requests.
2. **Token refresh**. The Claude Code OAuth access token expires every
   ~5 hours. Each `claude -p` invocation re-reads `~/.claude/.credentials.json`
   and refreshes silently — but only if the CLI runs at least once before
   the access token expires.
3. **Container health**. The img-worker container can crash (OOM, Docker
   restart, host network blip). Without a watchdog, every flyer request
   queues until you notice and `docker compose up -d`.

`scripts/setup_keep_alive.ps1` installs three Scheduled Tasks that handle
all three concerns. Run it once and forget it.

## Installation

Open an **elevated** PowerShell session at the project root:

```powershell
pwsh scripts/setup_keep_alive.ps1
```

Output should end with `Keep-alive setup complete.` Three tasks land in
`Task Scheduler` → `Task Scheduler Library`:

- `YakimaFlyer-PowerPolicy` — re-applies the `never sleep` AC power policy at logon.
- `YakimaFlyer-KeepAwake` — runs `scripts/keep_awake.ps1` continuously, sends a
  1-pixel mouse delta every 4 minutes via the Win32 `SendInput` API.
- `YakimaFlyer-Watchdog` — runs `scripts/watchdog.ps1` every 5 minutes;
  restarts the img-worker if it's down, exercises the Claude CLI auth so
  the refresh token stays warm.

The installer also applies the power-policy changes immediately:

```
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
```

## Logs

All three scripts log to `logs/` at the project root:

- `logs/keep_awake.log` — one line per heartbeat, `nudge ok` or the failure reason
- `logs/watchdog.log` — INFO/WARN/ERROR lines per tick
- `logs/watchdog.state.json` — running counters of consecutive misses

Tail with:

```powershell
Get-Content logs/watchdog.log -Tail 20 -Wait
```

## Failure modes

### "auth required" / Claude CLI returns 401

Means the OAuth refresh token has fully expired (typically after ~30 days
of no use). The watchdog logs `ERROR claude CLI auth likely expired`.

Fix: run `claude` interactively on the host (not inside the container).
The CLI will open a browser, you log in, the new token writes to
`%USERPROFILE%\.claude\.credentials.json`. The next `claude -p` invocation
inside the img-worker picks it up automatically because the container
mount is read-write.

### img-worker won't start

Watchdog logs `WARN img-worker not running — starting` and tries
`docker compose up -d img-worker`. If three consecutive ticks fail,
investigate manually:

```bash
docker compose logs img-worker --tail 200
docker compose ps
```

Common causes: Docker Desktop not running, mount path mismatch
(`%USERPROFILE%\.claude` doesn't exist), or out-of-disk on the WSL2 vhdx.

### Mouse jiggler interferes with screen recording / focus

Stop the task: `Stop-ScheduledTask -TaskName YakimaFlyer-KeepAwake`.
Power policy + watchdog still keep the machine alive (most modern hosts
on AC power don't actually need the jiggler; it's belt-and-suspenders for
laptops on idle-aggressive defaults).

## Tear down

When the flyer-generator backend swaps to Gemini (`FLYER_BACKEND=gemini`)
or whenever you want to stop the keep-alive entirely:

```powershell
pwsh scripts/setup_keep_alive.ps1 -Uninstall
```

That removes all three Scheduled Tasks. Power-policy overrides stay in
place — revert manually if you want OS-default sleep back:

```powershell
powercfg /change standby-timeout-ac 30
powercfg /change hibernate-timeout-ac 60
```

## What does NOT need to happen here

- **No custom OAuth refresh daemon.** The Claude Code CLI itself rotates
  access tokens on every invocation that finds an expiring one. The
  watchdog's hourly `claude -p "ok"` is the only refresh-cadence trigger
  needed.
- **No container-side Scheduled Task.** Everything host-side is
  PowerShell + Task Scheduler. The container itself just runs Celery and
  responds to incoming work.
- **No clock-skew syncing.** Docker Desktop on Windows uses host time.
- **No prod equivalent.** This entire document goes away when commercial
  swap flips `FLYER_BACKEND` to `gemini` or `anthropic_api`.
