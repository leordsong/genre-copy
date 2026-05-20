@echo off
chcp 65001 >nul
echo ============================================
echo   Moments Generator Build Script
echo ============================================
echo.

echo [1/3] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist\MomentsGenerator.exe del /f dist\MomentsGenerator.exe

echo [2/3] Building...
uv run pyinstaller MomentsGenerator.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo [3/3] Build completed!
echo.
echo Output: dist\MomentsGenerator.exe
for %%A in (dist\MomentsGenerator.exe) do echo Size: %%~zA bytes
echo.
echo Usage:
echo   1. Copy dist\MomentsGenerator.exe to target machine
echo   2. Run and configure API Key in Settings tab
echo   3. Config will be saved automatically
echo.
pause
