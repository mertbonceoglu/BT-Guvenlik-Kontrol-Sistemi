import time
import base64
import os
import ctypes
from core.config import FOTO_GENISLIK, FOTO_YUKSEKLIK, FOTO_JPEG_KALITE

# cv2 ve pyautogui sadece PC'de bulunur — Android APK'da yoktur
try:
    import cv2
    CV2_VAR = True
except ImportError:
    CV2_VAR = False

try:
    import pyautogui
    PYAUTOGUI_VAR = True
except ImportError:
    PYAUTOGUI_VAR = False

try:
    import psutil
    PSUTIL_VAR = True
except ImportError:
    PSUTIL_VAR = False

def _sarj_takili_mi():
    """Şarj kablosunun takılı olup olmadığını döndürür. Bilgi yoksa True (güvenli) döner."""
    if not PSUTIL_VAR:
        return True
    try:
        bat = psutil.sensors_battery()
        if bat is None:
            return True  # Masaüstü PC — kablo yok, bu özellik geçersiz
        return bat.power_plugged
    except Exception:
        return True

def fotograf_cek_ve_gonder(db_referans, ana_dizin, pusu_iptal=None):
    """Müdahale algılandığında pusuya yatıp 3 fotoğraf çeker (0, 3 ve 6. saniyede)."""
    if not PYAUTOGUI_VAR or not CV2_VAR:
        return  # Android'de çalışmaz

    print("\n[!] PC KİLİTLENDİ. Pusu modunda müdahale bekleniyor...")

    # Win+L kilit ekranının oturması için kısa bekleme
    time.sleep(1.5)
    ilk_konum = pyautogui.position()
    sarj_baslangic = _sarj_takili_mi()

    mudahale_turu = "MUDAHALE"  # Varsayılan

    while True:
        # Telefon geri geldiyse pusu modunu iptal et
        if pusu_iptal and pusu_iptal.is_set():
            print("\n[PUSU İPTAL] Telefon geri geldi, fotoğraf çekilmeyecek.")
            return

        # --- Şarj kablosu çıkarma kontrolü ---
        if sarj_baslangic and not _sarj_takili_mi():
            print("\n[!] ŞARJ KABLOSU ÇEKILDI!")
            mudahale_turu = "SARJ_CEKME"
            break

        # --- Klavye tuşlaması kontrolü (fareye göre öncelikli) ---
        izlenen_tuslar = [0x0D, 0x1B, 0x20]  # Enter, Esc, Space
        izlenen_tuslar += list(range(65, 91))  # A'dan Z'ye (65=A, 90=Z)
        
        for tus in izlenen_tuslar:
            if ctypes.windll.user32.GetAsyncKeyState(tus) & 0x8000:
                print("\n[!] Klavye tuşlaması algılandı!")
                mudahale_turu = "KLAVYE_DOKUNMA"
                break
        if mudahale_turu != "MUDAHALE":
            break

        # --- Fare hareketi kontrolü (50px tolerans) ---
        mevcut_konum = pyautogui.position()
        if abs(mevcut_konum[0] - ilk_konum[0]) > 50 or abs(mevcut_konum[1] - ilk_konum[1]) > 50:
            print("\n[!] Fare hareketi algılandı!")
            mudahale_turu = "FARE_HAREKETI"
            break

        time.sleep(0.1)

    # --- Kamerayı aç ---
    print("\n[!] Müdahale algılandı, kamera açılıyor...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Şarj çekilme olayı Windows tarafından zaten 2-3 saniye gecikmeli bildirildiği için,
        # bu olayda kameranın ışığa alışmasını (1.0sn) hiç beklemeden anında ilk kareyi alıyoruz.
        if mudahale_turu != "SARJ_CEKME":
            time.sleep(1.0)
        
        for _ in range(5): cap.read()

        # --- 3 fotoğraf çek: 0, 3 ve 6. saniyede ---
        os.makedirs(os.path.join(ana_dizin, "logs", "foto"), exist_ok=True)
        zaman_damgasi = time.strftime("%Y%m%d_%H%M%S")
        kareler = []

        for i in range(3):
            ret, frame = cap.read()
            if ret:
                dosya_adi = f"mudahale_{zaman_damgasi}_f{i+1}.jpg"
                yol = os.path.join(ana_dizin, "logs", "foto", dosya_adi)
                cv2.imwrite(yol, frame)
                kareler.append((frame, yol))
                print(f"[+] Fotoğraf {i+1}/3 kaydedildi: {dosya_adi}")
            if i < 2:
                time.sleep(3)  # 0 → 3 → 6. saniye
    finally:
        cap.release()

    simdiki_zaman = time.strftime("%H:%M:%S")
    tarih = time.strftime("%Y-%m-%d")

    if not kareler:
        print("[HATA] Kamera açılamadı veya fotoğraf çekilemedi!")
        # Kamera hatası da Firebase'e iletilir, kullanıcı telefonda görebilir
        try:
            db_referans('guvenlik_olayi').set({
                'durum': 'ALARM', 'foto': '',
                'zaman': simdiki_zaman, 'tarih': tarih, 'hata': 'KAMERA_HATASI'
            })
            db_referans('alarm_gecmisi').push({
                'zaman': simdiki_zaman, 'tarih': tarih,
                'foto': '', 'tip': 'KAMERA_HATASI'
            })
        except Exception as e:
            print(f"[HATA] Kamera hatası Firebase'e yazılamadı: {e}")
        if pusu_iptal: pusu_iptal.set()  # BT kontrol thread'ini durdur
        return

    # --- Eski fotoğrafları temizle (son 60 dosya = 20 müdahale × 3) ---
    try:
        foto_dizin = os.path.join(ana_dizin, "logs", "foto")
        dosyalar = sorted(
            [f for f in os.listdir(foto_dizin) if f.startswith("mudahale_")],
            reverse=True
        )
        for eski in dosyalar[60:]:
            os.remove(os.path.join(foto_dizin, eski))
    except Exception:
        pass

    # --- 3 fotoğrafı Firebase'e gönder ---
    print("[*] Fotoğraflar küçültülüp Firebase'e gönderiliyor...")
    fotolar = {}
    for i, (frame, _) in enumerate(kareler):
        frame_resized = cv2.resize(frame, (FOTO_GENISLIK, FOTO_YUKSEKLIK))
        _, buffer = cv2.imencode('.jpg', frame_resized, [int(cv2.IMWRITE_JPEG_QUALITY), FOTO_JPEG_KALITE])
        fotolar[f"foto_{i+1}"] = base64.b64encode(buffer).decode('utf-8')

    # Aktif alarm
    db_referans('guvenlik_olayi').set({
        'durum': 'ALARM',
        'foto': fotolar.get('foto_1', ''),
        'foto_2': fotolar.get('foto_2', ''),
        'foto_3': fotolar.get('foto_3', ''),
        'foto_sayisi': len(kareler),
        'zaman': simdiki_zaman,
        'tarih': tarih
    })

    # Geçmişe ekle (tüm fotoğraflar + müdahale türü)
    db_referans('alarm_gecmisi').push({
        'zaman': simdiki_zaman, 'tarih': tarih,
        'foto': fotolar.get('foto_1', ''),
        'foto_2': fotolar.get('foto_2', ''),
        'foto_3': fotolar.get('foto_3', ''),
        'foto_sayisi': len(kareler),
        'tip': mudahale_turu
    })

    # --- ntfy.sh üzerinden telefona bildirim (Push Notification) gönder ---
    try:
        from core.config import NTFY_KANAL_ADI
        import urllib.request
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_KANAL_ADI}",
            data="Bilgisayarina mudahale edildi! Uygulamadan hemen kontrol et.".encode('utf-8'),
            headers={
                "Title": "DIKKAT: PC Mudahalesi!",
                "Priority": "high",
                "Tags": "warning,rotating_light"
            }
        )
        urllib.request.urlopen(req, timeout=3)
        print("[*] Telefona bildirim (ntfy) gönderildi.")
    except Exception as e:
        print(f"[HATA] Bildirim gönderilemedi: {e}")

    # Firebase'de son 20 müdahaleyi tut, eskisini sil
    try:
        gecmis = db_referans('alarm_gecmisi').get()
        if isinstance(gecmis, dict) and len(gecmis) > 20:
            sirali = sorted(gecmis.keys())
            for key in sirali[:len(sirali) - 20]:
                db_referans(f'alarm_gecmisi/{key}').delete()
    except Exception:
        pass

    print(f"[TAMAM] {len(kareler)} fotoğraf Firebase'e iletildi. ({tarih} {simdiki_zaman})")

    # Pusu bitti, arka plandaki BT kontrol thread'ini de durdur
    if pusu_iptal: pusu_iptal.set()
