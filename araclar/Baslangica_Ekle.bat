@echo off
setlocal enabledelayedexpansion
title Baslangic Ayarlari

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=ProxiGuard Servisi.lnk"
set "VBS_PATH=%~dp0Servisi_Baslat_Gizli.vbs"

if "!STARTUP_FOLDER!"=="" (
    echo [HATA] Sistem degiskenleri okunamadi!
    pause
    exit /b
)

echo.
echo  --------------------------------------------
echo   ProxiGuard Servisi
echo   Baslangic Uygulama Ayarlari
echo  --------------------------------------------
echo.

if exist "%STARTUP_FOLDER%\%SHORTCUT_NAME%" (
    echo  [i] Servis su anda baslangica EKLI.
    echo.
    echo  1. Baslangictan KALDIR
    echo  2. Cikis
    echo.
    set /p "secim=  Seciminiz (1/2): "
    if "!secim!"=="1" (
        del "%STARTUP_FOLDER%\%SHORTCUT_NAME%"
        echo.
        echo  [OK] Baslangictan kaldirildi!
    ) else (
        echo.
        echo  [OK] Islem iptal edildi.
    )
) else (
    echo  [i] Servis su anda baslangica EKLI DEGIL.
    echo.
    echo  1. Baslangica EKLE
    echo  2. Cikis
    echo.
    set /p "secim=  Seciminiz (1/2): "
    if "!secim!"=="1" (
        REM VBS ve ICO yollarini tam mutlak yola cevir
        for %%I in ("%VBS_PATH%") do set "VBS_ABS_PATH=%%~fI"
        for %%I in ("%~dp0..\assets\icon.ico") do set "ICO_PATH=%%~fI"
        > "%TEMP%\CreateShortcut.vbs" (
            echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
            echo sLinkFile = "%STARTUP_FOLDER%\%SHORTCUT_NAME%"
            echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
            echo oLink.TargetPath = "wscript.exe"
            echo oLink.Arguments = """!VBS_ABS_PATH!"" 30"
            echo oLink.WorkingDirectory = "%~dp0.."
            echo oLink.Description = "ProxiGuard Servisi"
            echo oLink.IconLocation = "!ICO_PATH!, 0"
            echo oLink.Save
        )
        cscript //nologo "%TEMP%\CreateShortcut.vbs"
        del "%TEMP%\CreateShortcut.vbs"
        echo.
        echo  [OK] Baslangica eklendi! Bilgisayar acildiginda servis
        echo      otomatik olarak arka planda calisacak.
        echo      Sadece sistem tepsisinde kucuk bir ikon gorunecek.
        echo.
        echo  [i] NOT: Gorev Yoneticisi'nin Baslangic sekmesinde
        echo      "Windows Based Script Host" veya "wscript.exe"
        echo      olarak gorunur. Bu bizim ProxiGuard servisidir.
    ) else (
        echo.
        echo  [OK] Islem iptal edildi.
    )
)

echo.
pause
