@echo off

pushd %~dp0

setlocal enabledelayedexpansion

:: 1. Build HTML docs into local "build" folder
set "SRC=source"
set "OUT=build"
for /f "delims=" %%R in ('python -c "import sys,os;from pathlib import Path;src=Path(r'!SRC!');out=Path(r'!OUT!');newest=lambda p:max([f.stat().st_mtime for f in p.rglob('*') if f.is_file()]) if p.exists() and any(p.rglob('*')) else None; print('True' if newest(src) and (not out.exists() or newest(src) > newest(out)) else 'False')"') do set "SHOLDRUN=%%R"
if "!SHOLDRUN!"=="True" (
	sphinx-build -b html source build
)

:: 2. Copy the HTML output to assets folder
set "SRC=build"
set "DST=..\HighEnna-Graphical\source_files\assets\html"
for /f "delims=" %%R in ('python -c "import sys,os;from pathlib import Path;src=Path(r'!SRC!');dst=Path(r'!DST!');newest=lambda p:max([f.stat().st_mtime for f in p.rglob('*') if f.is_file()]) if p.exists() and any(p.rglob('*')) else None; print('True' if newest(src) and (not dst.exists() or newest(src) > newest(dst)) else 'False')"') do set "SHOULDRUN=%%R"
if "!SHOULDRUN!"=="True" (
    xcopy /E /I /Y "!SRC!" "!DST!" >nul
)

if not defined CALLED_FROM_PARENT (
	set FILE_PATH=..\HighEnna-Graphical\source_files\assets\html\index.html
	start "" "firefox" "!FILE_PATH!" || start "" "!FILE_PATH!"
)

endlocal

popd
