@echo off

pushd %~dp0

setlocal enabledelayedexpansion

:: 1. Check if pyinstaller exists, install if not
where pyinstaller >nul 2>&1
if !ERRORLEVEL! neq 0 (
    python -m pip install pyinstaller
)

:: 2. Ensure dependencies are up to date
set CALLED_FROM_PARENT=1
call ..\HighEnna-Backend\make.bat
call ..\HighEnna-Documentation\make.bat


:: 3. Build the project with pyinstaller
set "SRC=source_files"
set "OUT=build"
for /f "delims=" %%R in ('python -c "import sys,os;from pathlib import Path;src=Path(r'!SRC!');out=Path(r'!OUT!');newest=lambda p:max([f.stat().st_mtime for f in p.rglob('*') if f.is_file()]) if p.exists() and any(p.rglob('*')) else 0; print('True' if newest(src) and (not out.exists() or newest(src) > newest(out)) else 'False')"') do set "SHOLDRUN=%%R"
if "!SHOLDRUN!"=="True" (
    :: Clean previous build folder
    if exist build (
        rd /s /q build
    )

    :: Copy source files to build
    xcopy /E /I /H /Y source_files build >nul

    :: Change to build folder
    cd .\build

    :: Initial pyinstaller run
    pyinstaller main.py

    :: Copy assets to dist folder
    xcopy /E /I /H /Y  .\assets .\dist\assets >nul
    rem xcopy /E /I /H /Y  .\assets .\dist\assets >nul
    move /Y "assets\icons\icon.ico" "." >nul

    :: Build final onefile executable
    pyinstaller --name HighEnna --onefile --windowed --icon=.\icon.ico main.py

    :: Delete everything in current folder except "dist" and "build"
    for /d %%D in (*) do (
        if /i not "%%D"=="dist" if /i not "%%D"=="build" rd /s /q "%%D"
    )
    for %%F in (*) do (
        if /i not "%%F"=="build" if /i not "%%F"=="dist" del /f /q "%%F"
    )

    :: Move the .exe from dist to current folder
    for %%E in (dist\*.exe) do move /y "%%E" .  >nul
)


endlocal

popd