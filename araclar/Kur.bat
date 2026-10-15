@echo off
chcp 65001 >nul
title ProxiGuard - Kurulum

echo.
echo  ╔════════════════════════════════════════════════════╗
echo  ║   ProxiGuard: Bluetooth Tabanlı Güvenlik Sistemi - Kurulum  ║
echo  ╚═════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0.."

:: --- 1. Python kontrolü ---
echo  [1/4] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [HATA] Python bulunamadi!
    echo.
    echo  Lutfen asagidaki adrese gidip Python'u indirip kurun:
    echo  https://www.python.org/downloads/
    echo.
    echo  Kurulum sirasinda "Add Python to PATH" secenegini isaretleyin!
    echo.
    pause
    exit /b 1
)
python --version
echo  [OK] Python bulundu.
echo.

:: --- 2. firebase_key.json kontrolü ---
echo  [2/4] Firebase anahtar dosyasi kontrol ediliyor...
if not exist "core\firebase_key.json" (
    echo.
    echo  [HATA] core\firebase_key.json bulunamadi!
    echo  Bu dosya firebase veri tabanindan alinmalidir
    echo  Dosyayi core klasorune koyup tekrar calistirin.
    echo.
    pause
    exit /b 1
)
echo  [OK] Firebase anahtari bulundu.
echo.

:: --- 3. Sanal ortam ve kütüphaneler ---
echo  [3/4] Sanal ortam (venv) olusturuluyor...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo.
        echo  [HATA] Sanal ortam olusturulamadi!
        pause
        exit /b 1
    )
    echo  [OK] Sanal ortam olusturuldu.
) else (
    echo  [OK] Sanal ortam zaten mevcut.
)
echo.

echo  [4/4] Gerekli kutuphane ve bagimliliklar kuruluyor...
echo  (Bu islem internet baglantisi gerektirir, 2-5 dakika surebilir)
echo.

venv\Scripts\pip.exe install -r requirements-pc.txt

if %errorlevel% neq 0 (
    echo.
    echo  [HATA] Kutuphaneler kurulamadi. Internet baglantinizi kontrol edin.
    pause
    exit /b 1
)

echo.
echo  ════════════════════════════════════════════════════
echo  [TAMAM] Kurulum tamamlandi!
echo.
echo  BAGIMSIZ KULLANIM ICIN (kendi Firebase hesabinizla):
echo    1. firebase_baglanti.py dosyasini acin,
echo       FIREBASE_URL satirini kendi Firebase URL'inizle degistirin.
echo    2. Kendi firebase_key.json dosyanizi core klasorune koyun.
echo    3. Uygulamayi acin, Ayarlar sekmesinden kendi telefonunuzu eslesirin.
echo.
echo  Sistemi baslatmak icin:
echo    → Servisi_Baslat.bat dosyasina cift tiklayin
echo.
echo  Windows baslangicindan otomatik acmak icin:
echo    → Baslangiça_Ekle.bat dosyasina cift tiklayin
echo  ════════════════════════════════════════════════════
echo.
pause
