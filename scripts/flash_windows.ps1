#requires -version 5.1
# ESP32-S3 DIY240 — Windows PowerShell flasher for a verified CI artifact.
# Run from the extracted firmware folder: .\flash_windows.ps1 -Port COM5
param([Parameter(Mandatory=$true)][ValidatePattern('^COM[0-9]+$')][string]$Port)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root 'BUILD_INFO.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  throw 'BUILD_INFO.json missing. Extract the complete artifact ZIP.'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.board -ne 'DIY ESP32-S3 N16R8') {
  throw "Wrong board profile: $($manifest.board)"
}
$images = @(
  @{file='bootloader/bootloader.bin'; offset='0x0'},
  @{file='partition_table/partition-table.bin'; offset='0x8000'},
  @{file='furi_esp32.bin'; offset='0x10000'}
)
foreach($image in $images){
  $filename = Join-Path $root $image.file
  if (-not (Test-Path -LiteralPath $filename -PathType Leaf)) { throw "Missing image: $filename" }
  $records = @($manifest.images | Where-Object { $_.file -eq $image.file })
  if ($records.Count -ne 1 -or $records[0].offset -ne $image.offset) {
    throw "Unexpected mapping in BUILD_INFO.json: $($image.file)"
  }
  $sha = (Get-FileHash -LiteralPath $filename -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($sha -ne $records[0].sha256) { throw "SHA256 mismatch for $($image.file)" }
}
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python launcher 'py' not found. Install Python 3 for Windows."
}
& py -3 -m esptool version
if ($LASTEXITCODE -ne 0) {
  throw 'esptool missing. Install via: py -3 -m pip install "esptool>=4.8,<5"'
}
Write-Host "Target ESP32-S3 N16R8 at $Port"
Write-Warning 'This overwrites firmware, bootloader and partition information.'
$confirm=Read-Host 'Type FLASH to continue'
if ($confirm -cne 'FLASH') { Write-Host 'Cancelled.'; exit 1 }
Push-Location $root
try {
  & py -3 -m esptool --chip esp32s3 --port $Port --baud 460800 --before default_reset --after hard_reset write_flash 0x0 bootloader/bootloader.bin 0x8000 partition_table/partition-table.bin 0x10000 furi_esp32.bin
  if ($LASTEXITCODE -ne 0) { throw "esptool failed with status $LASTEXITCODE" }
  Write-Host 'Flash complete. Confirm screen, buttons, SD, and boot logs before declaring hardware verified.'
} finally { Pop-Location }
