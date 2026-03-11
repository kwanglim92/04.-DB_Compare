@echo off
echo ========================================================
echo      DB_Compare QC Tool v2.0 - Build Script
echo ========================================================
echo.

:: 1. Check for PyInstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller not found. Installing...
    pip install pyinstaller
)

:: 2. Clean previous builds
if exist "build" (
    echo [INFO] Cleaning build directory...
    rmdir /s /q "build"
)
if exist "dist" (
    echo [INFO] Cleaning dist directory...
    rmdir /s /q "dist"
)
if exist "*.spec" (
    del /q "*.spec"
)

:: 3. Check for Icon
set ICON_OPTION=
if exist "assets\icon.ico" (
    echo [INFO] Icon found! Using assets\icon.ico
    set ICON_OPTION=--icon="assets\icon.ico"
) else (
    echo [WARNING] Icon not found in assets\icon.ico. Using default icon.
    echo          Please place your icon file at: assets\icon.ico
)

:: 4. Run PyInstaller
echo.
echo [INFO] Starting build process...
echo        This may take a few minutes.
echo.

:: Build command for installer-based deployment
:: Config is NOT embedded - it will be external
:: --noconsole: Hide console window
:: --onefile: Create single executable
:: --name: Output filename
:: --add-data src: Include source code (required)
:: --collect-all: Include customtkinter resources

python -m PyInstaller --noconsole --onefile ^
    --name="DB_Compare_QC_Tool" ^
    %ICON_OPTION% ^
    --add-data "src;src" ^
    --collect-all customtkinter ^
    --hidden-import="openpyxl" ^
    --hidden-import="PIL" ^
    --hidden-import="PIL._tkinter_finder" ^
    main.py

:: 5. Check result
if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo [ERROR] Build failed. Please check the error messages.
    echo ========================================================
    pause
    exit /b 1
)

:: 6. Copy config files to dist for installer packaging
echo.
echo [INFO] Copying config files...
mkdir "dist\config"
mkdir "dist\config\profiles"
mkdir "dist\config\backup"

if exist "config\common_base.json" (
    copy "config\common_base.json" "dist\config\" >nul
    echo   - Copied common_base.json
)

if exist "config\profiles\*.json" (
    copy "config\profiles\*.json" "dist\config\profiles\" >nul
    echo   - Copied equipment profiles
)

if exist "config\settings.json" (
    copy "config\settings.json" "dist\config\" >nul
    echo   - Copied settings.json
)

:: 7. Summary
echo.
echo ========================================================
echo [SUCCESS] Build completed successfully!
echo.
echo Executable: dist\DB_Compare_QC_Tool.exe
echo Config:     dist\config\
echo.
echo Next steps:
echo   1. Run installer\build_installer.bat to create setup
echo   2. Or distribute the dist\ folder directly
echo ========================================================

:: Open dist folder
explorer dist

pause
