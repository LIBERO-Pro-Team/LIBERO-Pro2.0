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
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($file.FullName)
    try {
        $hash = [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
    } finally {
        $stream.Dispose()
        $algorithm.Dispose()
    }
    $relative = $file.FullName.Substring($rootPath.Length + 1).Replace('\', '/')
    "$hash  $relative"
}
$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
$content = if ($lines.Count -eq 0) { "" } else { ($lines -join "`n") + "`n" }
[IO.File]::WriteAllText($outputPath, $content, $utf8WithoutBom)
