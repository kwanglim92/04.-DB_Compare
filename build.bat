@echo off
echo ========================================================
echo      DB_Compare QC Inspection Tool - Build Script
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

:: Build command
:: --noconsole: Hide console window
:: --onefile: Create single executable
:: --name: Output filename
:: --add-data: Include config files
:: --collect-all: Include customtkinter resources

python -m PyInstaller --noconsole --onefile ^
    --name="DB_Compare_QC_Tool" ^
    %ICON_OPTION% ^
    --add-data "config;config" ^
    --add-data "src;src" ^
    --collect-all customtkinter ^
    --hidden-import="openpyxl" ^
    --hidden-import="PIL" ^
    --hidden-import="PIL._tkinter_finder" ^
    main.py

:: 5. Check result
if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo [SUCCESS] Build completed successfully!
    echo.
    echo Executable is located in: dist\DB_Compare_QC_Tool.exe
    echo ========================================================
    
    :: Open dist folder
    explorer dist
) else (
    echo.
    echo ========================================================
    echo [ERROR] Build failed. Please check the error messages.
    echo ========================================================
)

pause
