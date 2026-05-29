@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%src"
"c:\Users\Mohamed Zayaan\Downloads\Placement_Project\.venv\Scripts\python.exe" -m shmlrp %*
