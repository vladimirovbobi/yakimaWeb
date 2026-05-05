# keep_awake.ps1 — heartbeat that keeps the host awake.
#
# Sends a 1-pixel mouse delta via the Win32 SendInput API every 4 minutes.
# The cursor doesn't visibly move (the delta is too small for users to notice)
# but Windows registers user activity, defeating idle-sleep on hosts that
# can't be configured to "never sleep" via power policy alone.
#
# Logs to logs/keep_awake.log relative to the project root.
#
# Usage (interactive): pwsh scripts/keep_awake.ps1
# Usage (scheduled):   set up via scripts/setup_keep_alive.ps1
#
# Stop with Ctrl-C interactively, or `Stop-ScheduledTask` if running as a task.

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectRoot 'logs'
$LogFile = Join-Path $LogDir 'keep_awake.log'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

# Compile a tiny C# helper exposing user32!SendInput so PowerShell can
# generate a synthetic mouse-move event without launching another process.
$Signature = @'
using System;
using System.Runtime.InteropServices;
public static class Mouse {
    [StructLayout(LayoutKind.Sequential)]
    public struct INPUT { public uint type; public MOUSEKEYBDHARDWAREINPUT mkhi; }
    [StructLayout(LayoutKind.Explicit)]
    public struct MOUSEKEYBDHARDWAREINPUT { [FieldOffset(0)] public MOUSEINPUT mi; }
    [StructLayout(LayoutKind.Sequential)]
    public struct MOUSEINPUT {
        public int dx; public int dy; public uint mouseData;
        public uint dwFlags; public uint time; public IntPtr dwExtraInfo;
    }
    [DllImport("user32.dll", SetLastError = true)]
    public static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);
    public static void Nudge() {
        var input = new INPUT { type = 0 };
        input.mkhi.mi.dx = 1; input.mkhi.mi.dy = 0;
        input.mkhi.mi.dwFlags = 0x0001; // MOUSEEVENTF_MOVE
        SendInput(1, new[] { input }, Marshal.SizeOf(typeof(INPUT)));
    }
}
'@

if (-not ([Management.Automation.PSTypeName]'Mouse').Type) {
    Add-Type -TypeDefinition $Signature -Language CSharp
}

function Write-Log([string]$Message) {
    $line = "{0:yyyy-MM-ddTHH:mm:ssK}  {1}" -f (Get-Date), $Message
    Add-Content -Path $LogFile -Value $line
}

Write-Log "keep_awake started (pid=$PID, project=$ProjectRoot)"
$IntervalSeconds = 240
while ($true) {
    try {
        [Mouse]::Nudge()
        Write-Log "nudge ok"
    } catch {
        Write-Log "nudge failed: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds $IntervalSeconds
}
