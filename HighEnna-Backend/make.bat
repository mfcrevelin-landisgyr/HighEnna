@echo off

pushd %~dp0

setlocal enabledelayedexpansion

:: 1. Create VS folder and generate project if it doesn't exist
if not exist "VS" (
    mkdir "VS"
    cd "VS"
    cmake .. -G "Visual Studio 17 2022"
    cd ..
)

:: 2. Build the project with MSBuild
set "SRC=source_files"
set "OUT=VS\Release"
for /f "delims=" %%R in ('python -c "import sys,os;from pathlib import Path;src=Path(r'!SRC!');out=Path(r'!OUT!');newest=lambda p:max([f.stat().st_mtime for f in p.rglob('*') if f.is_file()]) if p.exists() and any(p.rglob('*')) else None; print('True' if newest(src) and (not out.exists() or newest(src) > newest(out)) else 'False')"') do set "SHOLDRUN=%%R"
if "!SHOLDRUN!"=="True" (
set "MSBUILD_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
"!MSBUILD_PATH!" "VS\HighEnnaBackend.sln" /p:Configuration=Release /p:Platform=x64
)

:: 3. Move the compiled .pyd if it exists
set "SRC=VS\Release\highennabackend.pyd"
set "DST=..\HighEnna-Graphical\source_files\highennabackend.pyd"
for /f "delims=" %%R in ('python -c "import os,sys;from pathlib import Path;src=Path(r'!SRC!');dst=Path(r'!DST!');print('True' if src.exists() and (not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime) else 'False')"') do set "SHOULDRUN=%%R"
if "!SHOULDRUN!"=="True" (
    copy /Y "!SRC!" "!DST!" >nul
)

endlocal

popd
