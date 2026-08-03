param(
    [string]$OutputRoot = "D:\LIBERO-Pro2.0-delivery",
    [string]$SimulatorRoot = "D:\LIBERO-PRO",
    [string]$Version = "1.0.0",
    [switch]$BuildImage
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$simRoot = (Resolve-Path $SimulatorRoot).Path
$output = [IO.Path]::GetFullPath($OutputRoot)
$bundleName = "libero-pro-bundle-$Version"
$bundleRoot = Join-Path $output $bundleName
$archive = Join-Path $output "$bundleName.tar.gz"
$staging = Join-Path $output ".staging-$bundleName"

function Convert-ToWslPath([string]$WindowsPath) {
    $fullPath = [IO.Path]::GetFullPath($WindowsPath)
    $root = [IO.Path]::GetPathRoot($fullPath)
    if ($root.Length -lt 2 -or $root[1] -ne ':') {
        throw "Only drive-letter paths can be mapped into WSL: $fullPath"
    }
    $drive = [char]::ToLowerInvariant($root[0])
    $relative = $fullPath.Substring($root.Length).Replace('\', '/')
    return "/mnt/$drive/$relative"
}

function Assert-ManifestBddlHashes($Manifest, [string]$AssetsRoot) {
    foreach ($task in $Manifest.tasks) {
        $bddl = Join-Path $AssetsRoot ($task.bddl_path -replace '/', '\')
        if (-not (Test-Path -LiteralPath $bddl)) { throw "Missing BDDL: $bddl" }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $bddl).Hash.ToLowerInvariant()
        if ($actual -ne $task.bddl_sha256) { throw "BDDL hash mismatch: $bddl" }
    }
}

if (-not $output.StartsWith([IO.Path]::GetPathRoot($output), [StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputRoot must resolve to an absolute path"
}

New-Item -ItemType Directory -Force $output | Out-Null
foreach ($target in @($bundleRoot, $staging)) {
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
if (Test-Path -LiteralPath $archive) {
    Remove-Item -LiteralPath $archive -Force
}

$serviceCommit = (git -C $repoRoot rev-parse HEAD).Trim()
$simulatorCommit = (git -C $simRoot rev-parse HEAD).Trim()
$expectedSimulatorCommit = "c02ee2c8255db1c36664fad978197c47e495f178"
if ($simulatorCommit -ne $expectedSimulatorCommit) {
    throw "Simulator commit mismatch: expected $expectedSimulatorCommit, got $simulatorCommit"
}
git -C $simRoot lfs fsck
if ($LASTEXITCODE -ne 0) { throw "Simulator Git LFS verification failed" }

$manifestPath = Join-Path $repoRoot "assets\task_manifest.json"
$manifest = Get-Content -Raw $manifestPath | ConvertFrom-Json
if ($manifest.task_count -ne 169 -or $manifest.tasks.Count -ne 169) {
    throw "Expected exactly 169 published BDDL entries"
}
Assert-ManifestBddlHashes $manifest (Split-Path $manifestPath)

New-Item -ItemType Directory -Force $staging | Out-Null
$sourceRoot = Join-Path $staging "source"
New-Item -ItemType Directory -Force $sourceRoot | Out-Null

$serviceArchive = Join-Path $staging "service.zip"
git -c core.autocrlf=false -C $repoRoot archive --format=zip --output=$serviceArchive HEAD
if ($LASTEXITCODE -ne 0) { throw "Failed to export committed service source" }
Expand-Archive -LiteralPath $serviceArchive -DestinationPath $sourceRoot
Remove-Item -LiteralPath $serviceArchive
Assert-ManifestBddlHashes $manifest (Join-Path $sourceRoot "assets")

$simDestination = Join-Path $sourceRoot "simulator-source"
if (Test-Path -LiteralPath $simDestination) { Remove-Item -LiteralPath $simDestination -Recurse -Force }
$excludeDirectories = @(
    ".git", ".codex-tmp", ".pytest_cache", ".ruff_cache", "__pycache__",
    "hust-vpn-logs", "images", "meeting_output", "runtime"
)
$excludeFiles = @(
    "Enable-CodexBypassRoutes.ps1", "Enable-HustSplitTunnel.ps1", "SplitTunnel-Usage.md"
)
$excludeDirectoryArgs = $excludeDirectories | ForEach-Object { "/XD", (Join-Path $simRoot $_) }
$excludeFileArgs = @("/XF") + $excludeFiles
$robocopyArguments = @($simRoot, $simDestination, "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:1", "/W:1")
$robocopyArguments += $excludeDirectoryArgs
$robocopyArguments += $excludeFileArgs
robocopy @robocopyArguments | Out-Null
if ($LASTEXITCODE -gt 7) { throw "Failed to copy simulator source (robocopy $LASTEXITCODE)" }

$wheelRoot = Join-Path $staging "wheels"
New-Item -ItemType Directory -Force $wheelRoot | Out-Null
& (Join-Path $repoRoot ".venv\Scripts\python.exe") -m pip wheel $repoRoot --no-deps --wheel-dir $wheelRoot
if ($LASTEXITCODE -ne 0) { throw "Wheel build failed" }
$sdkWheels = @(Get-ChildItem -LiteralPath $wheelRoot -Filter "libero_remote-$Version-*.whl")
if ($sdkWheels.Count -ne 1) { throw "Expected exactly one built SDK wheel" }
$clientCommonRequirements = @(
    "anyio==3.7.1",
    "certifi==2025.8.3",
    "exceptiongroup==1.3.0",
    "h11==0.14.0",
    "httpcore==0.17.3",
    "httpx==0.24.1",
    "idna==3.10",
    "sniffio==1.3.1",
    "typing_extensions==4.13.2"
)
$clientPythonVersions = @("38", "39", "310", "311", "312")
foreach ($pythonVersion in $clientPythonVersions) {
    $numpyRequirement = if ($pythonVersion -in @("38", "39")) {
        "numpy==1.22.4"
    } else {
        "numpy==1.26.4"
    }
    $downloadArguments = @(
        "-m", "pip", "download",
        "--dest", $wheelRoot,
        "--no-deps",
        "--only-binary=:all:",
        "--platform", "manylinux2014_x86_64",
        "--implementation", "cp",
        "--python-version", $pythonVersion,
        "--abi", "cp$pythonVersion",
        "msgpack==1.0.8",
        $numpyRequirement,
        "pydantic==1.10.22"
    )
    $downloadArguments += $clientCommonRequirements
    & (Join-Path $repoRoot ".venv\Scripts\python.exe") @downloadArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to build the offline SDK wheelhouse for CPython $pythonVersion"
    }
}

$imageRoot = Join-Path $staging "images"
New-Item -ItemType Directory -Force $imageRoot | Out-Null
$imageTar = Join-Path $imageRoot "libero-pro-server-$Version.tar"
$imageDigest = $null
if ($BuildImage) {
    $wslSource = Convert-ToWslPath $sourceRoot
    & wsl.exe -d Ubuntu -- test -f "$wslSource/Dockerfile"
    if ($LASTEXITCODE -ne 0) { throw "WSL cannot access Docker build context: $wslSource" }
    $buildArguments = @(
        "-u", "root", "-d", "Ubuntu", "--", "docker", "build",
        "--build-arg", "LIBERO_PRO_SOURCE=local",
        "--build-arg", "LIBERO_REMOTE_COMMIT=$serviceCommit",
        "--build-arg", "BASE_IMAGE=docker.m.daocloud.io/library/ubuntu:20.04",
        "--tag", "libero-pro-server:$Version", $wslSource
    )
    & wsl.exe @buildArguments
    if ($LASTEXITCODE -ne 0) { throw "Docker image build failed" }
    $imageDigest = (& wsl.exe -u root -d Ubuntu -- docker image inspect `
        --format "{{.Id}}" "libero-pro-server:$Version").Trim()
    if ($LASTEXITCODE -ne 0 -or $imageDigest -notmatch '^sha256:[0-9a-f]{64}$') {
        throw "Failed to resolve Docker image digest"
    }
    $wslImageTar = Convert-ToWslPath $imageTar
    & wsl.exe -u root -d Ubuntu -- docker save --output $wslImageTar "libero-pro-server:$Version"
    if ($LASTEXITCODE -ne 0) { throw "Docker image export failed" }
    Remove-Item -LiteralPath $sourceRoot -Recurse -Force
} else {
    Set-Content -Encoding ascii (Join-Path $imageRoot "BUILD_REQUIRED.txt") `
        "Run this script with -BuildImage on a Docker host to create the versioned image tar."
}

Copy-Item -Recurse -Force (Join-Path $repoRoot "deploy\customer-local\*") $staging
Copy-Item -Recurse -Force (Join-Path $repoRoot "assets") (Join-Path $staging "assets")
Copy-Item -Force (Join-Path $simRoot "LICENSE") (Join-Path $staging "LIBERO-LICENSE")
$documentRoot = Join-Path $staging "docs"
New-Item -ItemType Directory -Force $documentRoot | Out-Null
$customerDocumentManifest = Join-Path $PSScriptRoot "customer-documents.json"
$customerDocuments = Get-Content -LiteralPath $customerDocumentManifest `
    -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($document in $customerDocuments) {
    $documentSource = Join-Path $repoRoot "docs\$document"
    $documentDestination = Join-Path $documentRoot $document
    Copy-Item -LiteralPath $documentSource -Destination $documentDestination
}
New-Item -ItemType Directory -Force (Join-Path $staging "runtime"), (Join-Path $staging "logs") | Out-Null

$versionInfo = [ordered]@{
    bundle_version = $Version
    service_version = $Version
    sdk_version = $Version
    protocol_version = "1.0"
    benchmark_version = "libero-pro-2.0"
    service_commit = $serviceCommit
    simulator_commit = $simulatorCommit
    task_pack_version = $manifest.manifest_version
    perturbation_version = $manifest.manifest_version
    task_count = $manifest.task_count
    docker_image = if ($BuildImage) { "libero-pro-server:$Version" } else { $null }
    image_digest = $imageDigest
}
$versionInfo | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $staging "VERSION.json")

$checksumManifest = Join-Path $staging "SHA256SUMS"
& (Join-Path $PSScriptRoot "write_sha256_manifest.ps1") `
    -Root $staging -OutputFile $checksumManifest

Move-Item -LiteralPath $staging -Destination $bundleRoot
tar -czf $archive -C $output $bundleName
if ($LASTEXITCODE -ne 0) { throw "Bundle archive creation failed" }

$archiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
Set-Content -Encoding ascii "$archive.sha256" "$archiveHash  $bundleName.tar.gz"
Write-Output $bundleRoot
Write-Output $archive
