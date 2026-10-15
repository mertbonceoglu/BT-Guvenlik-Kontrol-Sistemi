@echo off
chcp 65001 >nul
title ProxiGuard Servisi
color 0A

echo.
echo  ════════════════════════════════════════════
echo   ProxiGuard Servisi
echo   Servis baslatiliyor, pencere kucultuluyor...
echo  ════════════════════════════════════════════
echo.

cd /d "%~dp0.."

:: Pencereyi minimize et 
if /i "%1" neq "min" (
    start /min "" "%~f0" min
    exit /b
)

if exist "venv\Scripts\python.exe" (
    echo  [OK] Sanal ortam bulundu, servis baslatiliyor...
    echo.
    venv\Scripts\python.exe bt_servis.py
) else (
    echo  [!] Sanal ortam bulunamadi, sistem Python kullaniliyor...
    echo.
    python bt_servis.py
)

echo.
echo  Servis durdu. Kapatmak icin bir tusa basin...
pause >nul
