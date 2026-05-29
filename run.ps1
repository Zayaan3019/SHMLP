$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root 'src'
& "c:\Users\Mohamed Zayaan\Downloads\Placement_Project\.venv\Scripts\python.exe" -m shmlrp @args
