@echo off
rem Double-cliquez sur ce fichier (Windows) pour ouvrir votre carnet de recettes.
rem Messages sans accents : la console Windows ne les affiche pas correctement par defaut.
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  if not exist "%USERPROFILE%\.local\bin\uv.exe" (
    echo Premier lancement : installation de uv, l'outil qui fait tourner le carnet de recettes...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  )
)
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo Lancement de votre carnet de recettes... il va s'ouvrir dans votre navigateur.
echo Gardez cette console ouverte pendant son utilisation. Fermez-la pour quitter.
uv run main.py
pause
