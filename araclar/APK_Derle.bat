@echo off
chcp 65001 >nul
title APK Derle
echo.
echo  APK Derleme - Mobil Uygulama
echo  Bu script Android APK dosyasi olusturur.
echo.
cd /d "%~dp0.."
echo  Eski build temizleniyor...
if exist "build" rd /s /q "build" 2>nul
echo.
echo  APK derleniyor... (5-10 dakika surebilir)
echo.
echo  Gereksiz venv dosyalarinin APK'ya dahil olmamasi icin gecici olarak gizleniyor...
if exist "venv" ren venv .venv

set PYTHONIOENCODING=utf-8
flet build apk --project "proxiguard" --product "ProxiGuard" --org com.proxiguard --build-version 2.0.0 --module-name main --yes --no-rich-output
set FLET_ERRORLEVEL=%errorlevel%

echo  Venv klasoru eski haline getiriliyor...
if exist ".venv" ren .venv venv

if %FLET_ERRORLEVEL% == 0 (
    echo.
    echo  [OK] APK basariyla derlendi!
    echo  [OK] Konum: build\apk\
) else (
    echo.
    echo  [HATA] Derleme basarisiz oldu.
)
echo.
pause
