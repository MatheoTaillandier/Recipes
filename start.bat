@echo off
rem Double-click this file (Windows) to open your recipe book.
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  if not exist "%USERPROFILE%\.local\bin\uv.exe" (
    echo First launch: installing uv, the tool that runs the recipe book...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  )
)
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo Starting your recipe book... it will open in your browser.
echo Keep this window open while you use it. Close it to stop.
uv run main.py
pause
