@echo off
echo ========================================================
echo      DB_Compare QC Tool - Installer Build Script
echo ========================================================
echo.

:: Check if Inno Setup is installed
set INNO_PATH=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    echo [ERROR] Inno Setup 6 not found!
    echo.
    echo Please install Inno Setup from:
    echo https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

:: Check if dist folder exists
if not exist "..\dist\DB_Compare_QC_Tool.exe" (
    echo [ERROR] Build not found!
    echo.
    echo Please run build.bat first to create the executable.
    echo.
    pause
    exit /b 1
)

:: Create output directory
if not exist "output" mkdir output

:: Build installer
echo [INFO] Building installer...
echo.

"%INNO_PATH%" setup.iss

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo [SUCCESS] Installer created successfully!
    echo.
    echo Installer: installer\output\DB_Compare_QC_Tool_Setup_v2.0.0.exe
    echo ========================================================
    
    explorer output
) else (
    echo.
    echo ========================================================
    echo [ERROR] Installer build failed.
    echo ========================================================
)

pause
