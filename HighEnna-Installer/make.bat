@echo off

pushd %~dp0

setlocal enabledelayedexpansion

:: 1. Ensure dependencies are up to date
set CALLED_FROM_PARENT=1
call ..\HighEnna-Graphical\make.bat

:: 2. Build the installer with Inno Setup 6
set "SRC=source_files"
set "OUT=output"
for /f "delims=" %%R in ('python -c "import sys,os;from pathlib import Path;src=Path(r'!SRC!');out=Path(r'!OUT!');newest=lambda p:max([f.stat().st_mtime for f in p.rglob('*') if f.is_file()]) if p.exists() and any(p.rglob('*')) else 0; print('True' if newest(src) and (not out.exists() or newest(src) > newest(out)) else 'False')"') do set "SHOLDRUN=%%R"
if "!SHOLDRUN!"=="True" (
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" .\source_files\setup_compile_script.iss
)

endlocal

popd