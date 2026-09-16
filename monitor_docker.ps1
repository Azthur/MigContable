# Monitor de recursos Docker — SistemaMigConta
# Muestra docker stats cada $IntervalSec segundos y los guarda en monitor_docker.log
# Detecta: uso de memoria > $WarnPct del limite, OOMKilled y reinicios.
#
# Uso:   powershell -File monitor_docker.ps1
#        powershell -File monitor_docker.ps1 -IntervalSec 15 -WarnPct 85
# Detener: Ctrl+C

param(
    [int]$IntervalSec = 30,
    [int]$WarnPct = 80,
    [string]$LogFile = "monitor_docker.log",
    [int]$MaxLogMB = 20          # rotacion: cuando supera este tamano se compacta
)

$ErrorActionPreference = "SilentlyContinue"
$logPath = Join-Path $PSScriptRoot $LogFile
if (-not $PSScriptRoot) { $logPath = $LogFile }

Write-Host "Monitoreando contenedores cada ${IntervalSec}s -> $logPath (Ctrl+C para salir)"
"===== inicio monitor $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') =====" | Out-File $logPath -Append

# Snapshot inicial de estado OOM/restarts
$prevRestarts = @{}

function Invoke-LogRotation {
    # Mantiene el log acotado: si supera $MaxLogMB, conserva solo la mitad
    # mas reciente (max ~2 x MaxLogMB en disco, sin acumulacion infinita)
    $f = Get-Item $logPath -ErrorAction SilentlyContinue
    if ($f -and $f.Length -gt ($MaxLogMB * 1MB)) {
        $tail = Get-Content $logPath -Tail 5000
        Move-Item $logPath "$logPath.old" -Force
        "===== rotado $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') =====" | Out-File $logPath
        $tail | Out-File $logPath -Append
    }
}

while ($true) {
    Invoke-LogRotation
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

    # docker stats --no-stream: NAME, MEM USAGE / LIMIT, MEM %, CPU %, NET I/O, BLOCK I/O, PIDS
    $stats = docker stats --no-stream --format "{{.Name}}|{{.MemUsage}}|{{.MemPerc}}|{{.CPUPerc}}" 2>$null
    foreach ($line in $stats) {
        $parts = $line -split '\|'
        if ($parts.Count -lt 4) { continue }
        $name, $memUsage, $memPerc, $cpuPerc = $parts[0], $parts[1], $parts[2], $parts[3]
        $entry = "$ts  $name  mem=$memUsage  mem%=$memPerc  cpu=$cpuPerc"
        $entry | Out-File $logPath -Append

        $pctNum = [double]($memPerc -replace '[^0-9\.]', '')
        if ($pctNum -ge $WarnPct) {
            $msg = "$ts  *** MEMORIA CRITICA: $name al ${memPerc} del limite ($memUsage) ***"
            Write-Host $msg -ForegroundColor Red
            $msg | Out-File $logPath -Append
        }

        # Detectar OOMKilled / cambios en RestartCount
        $insp = docker inspect $name --format "{{.State.OOMKilled}}|{{.RestartCount}}|{{.State.Status}}" 2>$null
        if ($insp) {
            $oom, $rc, $status = $insp -split '\|'
            if ($oom -eq 'true') {
                $msg = "$ts  *** OOMKilled detectado en $name (status=$status) ***"
                Write-Host $msg -ForegroundColor Red
                $msg | Out-File $logPath -Append
            }
            $rcNum = [int]$rc
            if ($prevRestarts.ContainsKey($name) -and $rcNum -gt $prevRestarts[$name]) {
                $msg = "$ts  *** REINICIO: $name paso de $($prevRestarts[$name]) a $rcNum reinicios ***"
                Write-Host $msg -ForegroundColor Yellow
                $msg | Out-File $logPath -Append
            }
            $prevRestarts[$name] = $rcNum
        }
    }

    # Memoria del host (para correlacionar con presion de WSL/vmmem)
    $os = Get-CimInstance Win32_OperatingSystem
    $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    $totGB  = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    "$ts  HOST mem libre=$freeGB/$totGB GB" | Out-File $logPath -Append

    $vmmem = Get-Process vmmem* -ErrorAction SilentlyContinue |
             Measure-Object WorkingSet64 -Sum | Select-Object -Expand Sum
    if ($vmmem) {
        "$ts  WSL vmmem=$([math]::Round($vmmem/1GB,2))GB" | Out-File $logPath -Append
    }

    Start-Sleep -Seconds $IntervalSec
}
