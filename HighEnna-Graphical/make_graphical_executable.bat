@echo off

setlocal

where pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    python -m pip install pyinstaller
)

if exist .\build (
    rd /s /q .\build
)

xcopy /E /I /H /Y .\source_files .\build

cd .\build

pyinstaller main.py
xcopy /E /I /H /Y  .\assets .\dist\assets
xcopy /E /I /H /Y  .\assets .\dist\assets
pyinstaller --name HighEnna --onefile --windowed --icon=.\icon.ico main.py

if exist .\dist\HighEnna.exe (
    move .\dist\HighEnna.exe .
)

endlocal
