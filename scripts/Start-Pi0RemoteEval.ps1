[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu",
    [string]$WslPython = "/home/vla/venvs/lerobot-xvla312/bin/python",
    [string]$LeRobotRoot = "D:\lerobot",
    [string]$ModelPath = "D:\models\pi0-libero-finetuned-v044",
    [string]$TokenizerPath = "D:\models\paligemma-3b-pt-224",
    [string]$ServerHost = "222.20.126.33",
    [string]$ServerUser = "zhouxueyang",
    [int]$LocalPort = 18082,
    [int]$RemotePort = 8000,
    [string]$Suite = "libero_spatial",
    [int]$TaskId = 8,
    [int]$InitStateId = 0,
    [int]$Episodes = 1,
    [int]$Seed = 142,
    [int]$MaxSteps = 500,
    [string]$Variant = "base",
    [double]$Timeout = 120,
    [string]$Output = "runtime\pi0_remote_eval_spatial_task8_clean.jsonl",
    [switch]$NoTunnel
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$route = (& wsl.exe -d $Distro -- ip route show default | Select-Object -First 1)
if (-not $route) {
    throw "Cannot determine the Windows gateway address from WSL distro '$Distro'."
}
$routeParts = $route.Trim() -split "\s+"
$gateway = $routeParts[2]
$baseUrl = "http://${gateway}:${LocalPort}"
$startedTunnel = $null

function Convert-ToWslPath([string]$WindowsPath) {
    $absolute = [IO.Path]::GetFullPath($WindowsPath)
    $portable = $absolute.Replace("\", "/")
    $converted = & wsl.exe -d $Distro -- wslpath -a $portable
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot convert Windows path for WSL: $WindowsPath"
    }
    return $converted.Trim()
}

function Test-RemoteHealth {
    $probe = "import json,urllib.request; print(json.load(urllib.request.urlopen('${baseUrl}/v1/health', timeout=3))['status'])"
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $result = & wsl.exe -d $Distro -- $WslPython -c $probe 2>$null
        $probeExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
    return $probeExitCode -eq 0 -and ($result | Select-Object -Last 1) -eq "ok"
}

try {
    & wsl.exe -d $Distro -- $WslPython -c "import httpx, msgpack, torch, transformers" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "WSL Pi0 environment is missing required client or model dependencies."
    }

    if (-not (Test-RemoteHealth)) {
        if ($NoTunnel) {
            throw "Remote service is not reachable from WSL at $baseUrl."
        }
        $listener = Get-NetTCPConnection `
            -State Listen `
            -LocalPort $LocalPort `
            -ErrorAction SilentlyContinue
        if ($listener) {
            $replacementPort = $null
            for ($candidate = $LocalPort + 1; $candidate -le $LocalPort + 20; $candidate++) {
                $candidateListener = Get-NetTCPConnection `
                    -State Listen `
                    -LocalPort $candidate `
                    -ErrorAction SilentlyContinue
                if (-not $candidateListener) {
                    $replacementPort = $candidate
                    break
                }
            }
            if ($null -eq $replacementPort) {
                throw "The requested tunnel port is stale and no fallback port is available."
            }
            $LocalPort = $replacementPort
            $baseUrl = "http://${gateway}:${LocalPort}"
        }

        $forward = "${gateway}:${LocalPort}:127.0.0.1:${RemotePort}"
        $sshArgs = @(
            "-N",
            "-o", "BatchMode=yes",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "ServerAliveInterval=30",
            "-L", $forward,
            "${ServerUser}@${ServerHost}"
        )
        $startedTunnel = Start-Process `
            -FilePath "ssh.exe" `
            -ArgumentList $sshArgs `
            -PassThru `
            -WindowStyle Hidden

        $ready = $false
        for ($attempt = 0; $attempt -lt 20; $attempt++) {
            Start-Sleep -Milliseconds 500
            if ($startedTunnel.HasExited) {
                throw "SSH tunnel exited before the remote service became reachable."
            }
            if (Test-RemoteHealth) {
                $ready = $true
                break
            }
        }
        if (-not $ready) {
            throw "SSH tunnel started, but $baseUrl did not become healthy."
        }
    }

    $repoWsl = Convert-ToWslPath $repoRoot
    $lerobotWsl = Convert-ToWslPath $LeRobotRoot
    $modelWsl = Convert-ToWslPath $ModelPath
    $tokenizerWsl = Convert-ToWslPath $TokenizerPath
    $outputPath = if ([IO.Path]::IsPathRooted($Output)) {
        $Output
    } else {
        Join-Path $repoRoot $Output
    }
    $outputParent = Split-Path -Parent $outputPath
    if ($outputParent) {
        New-Item -ItemType Directory -Force -Path $outputParent | Out-Null
    }
    $outputWsl = Convert-ToWslPath $outputPath
    $runnerWsl = "${repoWsl}/scripts/run_pi0_remote_eval.py"
    $pythonPath = "${repoWsl}:${lerobotWsl}/src"

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & wsl.exe -d $Distro -- env "PYTHONPATH=$pythonPath" $WslPython $runnerWsl `
            --base-url $baseUrl `
            --lerobot-root $lerobotWsl `
            --model-path $modelWsl `
            --tokenizer-path $tokenizerWsl `
            --suite $Suite `
            --task-id $TaskId `
            --init-state-id $InitStateId `
            --episodes $Episodes `
            --seed $Seed `
            --max-steps $MaxSteps `
            --variant $Variant `
            --timeout $Timeout `
            --output $outputWsl
        $runnerExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
    if ($runnerExitCode -ne 0) {
        throw "Pi0 remote evaluation exited with code $runnerExitCode."
    }
} finally {
    if ($null -ne $startedTunnel -and -not $startedTunnel.HasExited) {
        Stop-Process -Id $startedTunnel.Id
    }
}
