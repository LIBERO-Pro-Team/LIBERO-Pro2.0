param(
    [Parameter(Mandatory = $true)]
    [string]$Root,
    [Parameter(Mandatory = $true)]
    [string]$OutputFile
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$outputPath = [IO.Path]::GetFullPath($OutputFile)
$files = Get-ChildItem -LiteralPath $rootPath -Recurse -File | Where-Object {
    $_.FullName -ne $outputPath
} | Sort-Object FullName
$lines = foreach ($file in $files) {
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLowerInvariant()
    $relative = $file.FullName.Substring($rootPath.Length + 1).Replace('\', '/')
    "$hash  $relative"
}
$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllLines($outputPath, $lines, $utf8WithoutBom)
