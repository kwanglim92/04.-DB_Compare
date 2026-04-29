@echo off
echo ========================================================
echo      DB_Compare QC Tool v1.1.0 - Build Script
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

:: 3. Check for Icon
set ICON_OPTION=
if exist "assets\icon.ico" (
    echo [INFO] Icon found! Using assets\icon.ico
    set ICON_OPTION=--icon="assets\icon.ico"
) else (
    echo [WARNING] Icon not found in assets\icon.ico. Using default icon.
)

:: 4. Run PyInstaller — Single EXE with embedded config
echo.
echo [INFO] Starting build process...
echo        Building single EXE with embedded config files.
echo        This may take a few minutes.
echo.

:: --onefile:       Single executable
:: --noconsole:     Hide console window
:: --add-data src:  Include source code
:: --add-data config: Embed config files inside EXE
:: --collect-all:   Include customtkinter resources

python -m PyInstaller --noconsole --onefile ^
    --name="DB_Compare_QC_Tool" ^
    %ICON_OPTION% ^
    --add-data "src;src" ^
    --add-data "config;config" ^
    --collect-all customtkinter ^
    --hidden-import="openpyxl" ^
    --hidden-import="PIL" ^
    --hidden-import="PIL._tkinter_finder" ^
    --hidden-import="psycopg2" ^
    --hidden-import="psycopg2._psycopg" ^
    --hidden-import="cryptography" ^
    --hidden-import="cryptography.fernet" ^
    --hidden-import="rapidfuzz" ^
    --hidden-import="rapidfuzz.fuzz" ^
    --hidden-import="rapidfuzz.process" ^
    --hidden-import="rapidfuzz.utils" ^
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

:: 6. Summary
echo.
echo ========================================================
echo [SUCCESS] Build completed successfully!
echo.
echo   Output: dist\DB_Compare_QC_Tool.exe
echo.
echo   Config files are EMBEDDED inside the EXE.
echo   No external config folder needed!
echo   Field modifications reset on restart (by design).
echo ========================================================

:: Open dist folder
explorer dist

pause
