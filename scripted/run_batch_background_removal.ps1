$ErrorActionPreference = "Stop"

$workspace = "C:\Dev\Image generator"
$pythonPath = "C:\Users\bp303\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\python.exe"
$scriptPath = Join-Path $workspace "scripted\remove_black_bg.py"
$inputDir = Join-Path $workspace "input"
$outputDir = Join-Path $workspace "output\batch"
$env:PYTHONPATH = Join-Path $workspace ".venv\Lib\site-packages"

& $pythonPath `
  $scriptPath `
  --input-dir $inputDir `
  --output-dir $outputDir `
  --preset ui-soft `
  --split-components `
  --crop-transparent-bounds `
  --asset-subfolders

Write-Host ""
Write-Host "Batch background removal finished."
Write-Host "Output folder: $outputDir"
