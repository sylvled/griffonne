# Lance Griffonne (dictée vocale locale)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\python.exe" -m griffonne.app
