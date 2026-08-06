[CmdletBinding()]
param(
    [string]$OutputRoot,
    [string]$ServiceRepository,
    [string]$SimulatorRepository,
    [string]$BaselinePath
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repositoryRoot "dist-conda"
}
if (-not $ServiceRepository) {
    $ServiceRepository = $repositoryRoot
}
if (-not $SimulatorRepository) {
    if ($env:LIBERO_PRO_SOURCE_REPOSITORY) {
        $SimulatorRepository = $env:LIBERO_PRO_SOURCE_REPOSITORY
    } else {
        $SimulatorRepository = Join-Path (Split-Path -Parent $repositoryRoot) "LIBERO-PRO"
    }
}
if (-not $BaselinePath) {
    $BaselinePath = Join-Path $repositoryRoot "deploy\customer-conda\SOURCE_BASELINE.json"
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

function Invoke-NativeText {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $output = & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
    return (($output | Out-String).Trim())
}

function Write-Utf8Lf {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $normalized = $Content.Replace("`r`n", "`n").Replace("`r", "`n")
    if (-not $normalized.EndsWith("`n")) {
        $normalized += "`n"
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $normalized, $encoding)
}

function Get-RelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $rootPath = [System.IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $fullPath.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the bundle root: $fullPath"
    }
    return $fullPath.Substring($rootPath.Length).Replace('\', '/')
}

function Write-HashManifest {
    param(
        [Parameter(Mandatory = $true)][string]$BundleRoot,
        [Parameter(Mandatory = $true)][string]$OutputFile,
        [string[]]$IncludedDirectories
    )
    $files = @()
    if ($IncludedDirectories) {
        foreach ($directory in $IncludedDirectories) {
            $files += Get-ChildItem -LiteralPath (Join-Path $BundleRoot $directory) -File -Recurse
        }
    } else {
        $files = Get-ChildItem -LiteralPath $BundleRoot -File -Recurse |
            Where-Object { $_.FullName -ne $OutputFile }
    }
    $records = foreach ($file in $files) {
        $relative = Get-RelativePath -Root $BundleRoot -Path $file.FullName
        $digest = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        [PSCustomObject]@{ Relative = $relative; Line = "$digest  $relative" }
    }
    $content = (($records | Sort-Object Relative | ForEach-Object { $_.Line }) -join "`n")
    Write-Utf8Lf -Path $OutputFile -Content $content
}

function Export-GitCommit {
    param(
        [Parameter(Mandatory = $true)][string]$Repository,
        [Parameter(Mandatory = $true)][string]$Commit,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][string]$TemporaryArchive
    )
    Invoke-Native -Command "git" -Arguments @(
        "-C", $Repository, "cat-file", "-e", "$Commit^{commit}"
    )
    Invoke-Native -Command "git" -Arguments @(
        "-C", $Repository, "-c", "core.autocrlf=false", "archive",
        "--format=zip", "--output=$TemporaryArchive", $Commit
    )
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Expand-Archive -LiteralPath $TemporaryArchive -DestinationPath $Destination -Force
}

function Test-LfsPointer {
    param([Parameter(Mandatory = $true)][string]$Path)
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $buffer = New-Object byte[] 80
        $count = $stream.Read($buffer, 0, $buffer.Length)
        $prefix = [System.Text.Encoding]::ASCII.GetString($buffer, 0, $count)
        return $prefix.StartsWith("version https://git-lfs.github.com/spec/v1")
    } finally {
        $stream.Dispose()
    }
}

$ServiceRepository = (Resolve-Path -LiteralPath $ServiceRepository).Path
$SimulatorRepository = (Resolve-Path -LiteralPath $SimulatorRepository).Path
$BaselinePath = (Resolve-Path -LiteralPath $BaselinePath).Path
$templateRoot = Join-Path $repositoryRoot "deploy\customer-conda"
if (-not (Test-Path -LiteralPath $templateRoot -PathType Container)) {
    throw "Conda delivery template is missing: $templateRoot"
}
$baseline = Get-Content -LiteralPath $BaselinePath -Raw -Encoding UTF8 | ConvertFrom-Json
$requiredBaselineFields = @(
    "reference_version", "service_commit", "simulator_commit", "reference_image",
    "reference_image_digest", "python_version", "task_count"
)
foreach ($field in $requiredBaselineFields) {
    if (-not $baseline.$field) {
        throw "SOURCE_BASELINE.json is missing: $field"
    }
}

$simulatorHead = Invoke-NativeText -Command "git" -Arguments @(
    "-C", $SimulatorRepository, "rev-parse", "HEAD"
)
if ($simulatorHead -ne $baseline.simulator_commit) {
    throw "Simulator HEAD $simulatorHead does not match $($baseline.simulator_commit)"
}
Invoke-Native -Command "git" -Arguments @(
    "-C", $SimulatorRepository, "diff", "--quiet", $baseline.simulator_commit, "--"
)
Invoke-Native -Command "git" -Arguments @(
    "-C", $SimulatorRepository, "lfs", "fsck", $baseline.simulator_commit
)

$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$bundleName = "libero-pro-conda-bundle-$($baseline.reference_version)"
$bundlePath = Join-Path $OutputRoot $bundleName
$stagingPath = Join-Path $OutputRoot ".$bundleName.staging"
$archivePath = Join-Path $OutputRoot "$bundleName.tar.gz"
$archiveManifestPath = "$archivePath.sha256"
$serviceArchive = Join-Path $OutputRoot ".$bundleName.service.zip"
$simulatorArchive = Join-Path $OutputRoot ".$bundleName.simulator.zip"

foreach ($path in @($bundlePath, $stagingPath, $archivePath, $archiveManifestPath)) {
    $full = [System.IO.Path]::GetFullPath($path)
    $parent = [System.IO.Path]::GetDirectoryName($full)
    if ($parent -ne $OutputRoot) {
        throw "Refusing to replace a path outside the output root: $full"
    }
    if (Test-Path -LiteralPath $full) {
        Remove-Item -LiteralPath $full -Recurse -Force
    }
}
New-Item -ItemType Directory -Path $stagingPath | Out-Null

try {
    Get-ChildItem -LiteralPath $templateRoot -Force | ForEach-Object {
        if ($_.Name -notin @("server.env", "client.env", "runtime", "logs")) {
            Copy-Item -LiteralPath $_.FullName -Destination $stagingPath -Recurse -Force
        }
    }
    Copy-Item -LiteralPath $BaselinePath -Destination (
        Join-Path $stagingPath "SOURCE_BASELINE.json"
    ) -Force

    Export-GitCommit `
        -Repository $ServiceRepository `
        -Commit $baseline.service_commit `
        -Destination (Join-Path $stagingPath "service-source") `
        -TemporaryArchive $serviceArchive
    Export-GitCommit `
        -Repository $SimulatorRepository `
        -Commit $baseline.simulator_commit `
        -Destination (Join-Path $stagingPath "simulator-source") `
        -TemporaryArchive $simulatorArchive

    $lfsPaths = @(& git -C $SimulatorRepository lfs ls-files --name-only)
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to enumerate simulator Git LFS files."
    }
    foreach ($relative in $lfsPaths) {
        if (-not $relative) {
            continue
        }
        $source = Join-Path $SimulatorRepository $relative
        $destination = Join-Path (Join-Path $stagingPath "simulator-source") $relative
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Git LFS entity is missing from the simulator worktree: $relative"
        }
        $destinationParent = Split-Path -Parent $destination
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination -Force
        if (Test-LfsPointer -Path $destination) {
            throw "Git LFS pointer was not materialized: $relative"
        }
    }

    $serviceFileCount = @(
        Get-ChildItem -LiteralPath (Join-Path $stagingPath "service-source") -File -Recurse
    ).Count
    $simulatorFileCount = @(
        Get-ChildItem -LiteralPath (Join-Path $stagingPath "simulator-source") -File -Recurse
    ).Count
    $version = [ordered]@{
        bundle_version = [string]$baseline.reference_version
        build_format = "conda-source-v1"
        service_commit = [string]$baseline.service_commit
        simulator_commit = [string]$baseline.simulator_commit
        reference_image = [string]$baseline.reference_image
        reference_image_digest = [string]$baseline.reference_image_digest
        python_version = [string]$baseline.python_version
        task_count = [int]$baseline.task_count
        service_source_file_count = $serviceFileCount
        simulator_source_file_count = $simulatorFileCount
    }
    Write-Utf8Lf -Path (Join-Path $stagingPath "VERSION.json") -Content (
        $version | ConvertTo-Json -Depth 5
    )
    Write-HashManifest `
        -BundleRoot $stagingPath `
        -OutputFile (Join-Path $stagingPath "SOURCE_SHA256SUMS") `
        -IncludedDirectories @("service-source", "simulator-source")
    Write-HashManifest `
        -BundleRoot $stagingPath `
        -OutputFile (Join-Path $stagingPath "SHA256SUMS")

    Move-Item -LiteralPath $stagingPath -Destination $bundlePath
    Invoke-Native -Command "tar.exe" -Arguments @(
        "-czf", $archivePath, "-C", $OutputRoot, $bundleName
    )
    $archiveDigest = (
        Get-FileHash -LiteralPath $archivePath -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    Write-Utf8Lf -Path $archiveManifestPath -Content (
        "$archiveDigest  $([System.IO.Path]::GetFileName($archivePath))"
    )
} finally {
    foreach ($temporaryArchive in @($serviceArchive, $simulatorArchive)) {
        if (Test-Path -LiteralPath $temporaryArchive) {
            Remove-Item -LiteralPath $temporaryArchive -Force
        }
    }
}

Write-Output "Bundle: $bundlePath"
Write-Output "Archive: $archivePath"
Write-Output "Archive checksum: $archiveManifestPath"
