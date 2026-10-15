import asyncio
import collections
import time
import ctypes
import threading
import os
import sys
import subprocess
from bleak import BleakScanner

from core.firebase_baglanti import db_referans
from core.config import HEDEF_BT_ADRES as _VARSAYILAN_ADRES, ONAY_SURESI, SINYAL_KOPMA_SURESI
from servis.sistem_izleyici import sistem_bilgilerini_guncelle
from servis.kamera_motoru import fotograf_cek_ve_gonder
from servis.sistem_tepsisi import sistem_tepsisi_ikonu_baslat

try:
    import pyautogui
    PYAUTOGUI_VAR = True
except ImportError:
    PYAUTOGUI_VAR = False

# --- 1. SABİTLER ---
ANA_DIZIN = os.path.dirname(os.path.abspath(__file__))
SISTEM_GUNCELLEME_ARALIGI = 3

# --- 2. SERVİS DURUMU (tüm değişken state tek yerde) ---
class ServisDurumu:
    """Servisin tüm değişken durumunu thread-safe şekilde tutan sınıf."""
    def __init__(self):
        self._lock = threading.Lock()
        self.hedef_adres = _VARSAYILAN_ADRES
        self.rssi_gecmisi = collections.deque(maxlen=30)
        self.son_gorulme_zamani = time.time()
        self.zayif_sinyal_kronometresi = 0
        self.kilitlendi_mi = False
        self.kilit_aktif = False
        self.kilit_esik = -75.0
        self.servis_hazir = False
        self.pusu_iptal = threading.Event()
        self._son_bt_yazma = 0
        self._son_bt_durum = ""

durum = ServisDurumu()

# --- 3. YARDIMCI FONKSİYONLAR ---
def bilgisayari_kilitle():
    ctypes.windll.user32.LockWorkStation()

def bluetooth_durumu_guncelle(bt_durum, rssi=None, esik=None, zorla=False):
    simdi = time.time()
    # Aynı durumdaysa ve 5 saniye geçmediyse Firebase'e yazma (kota tasarrufu)
    if not zorla and bt_durum == durum._son_bt_durum and (simdi - durum._son_bt_yazma) < 5:
        return
    durum._son_bt_yazma = simdi
    durum._son_bt_durum = bt_durum
    veri = {
        'durum': bt_durum,
        'son_gorulme': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if rssi is not None: veri['rssi'] = round(rssi, 1)
    if esik is not None: veri['esik'] = round(esik, 1)
    try:
        db_referans('bluetooth').set(veri)
    except Exception as e:
        print(f"[HATA] BT durum güncellenemedi: {e}")

def tarama_callback(device, adv):
    if device.address.upper() == durum.hedef_adres:
        durum.rssi_gecmisi.append(adv.rssi)
        durum.son_gorulme_zamani = time.time()

def pusu_sirasinda_bt_kontrol():
    """Pusu modundayken telefon güvenli mesafeye geri geldi mi diye BT taraması yapar."""
    async def _kontrol():
        while not durum.pusu_iptal.is_set():
            rssi_degerleri = []
            def cb(device, adv):
                if device.address.upper() == durum.hedef_adres:
                    rssi_degerleri.append(adv.rssi)
            scanner = BleakScanner(detection_callback=cb)
            await scanner.start()
            await asyncio.sleep(3)
            await scanner.stop()
            if rssi_degerleri:
                ortalama = sum(rssi_degerleri) / len(rssi_degerleri)
                if ortalama >= durum.kilit_esik:
                    print(f"\n[PUSU] Telefon güvenli mesafede! (RSSI: {ortalama:.1f} >= Eşik: {durum.kilit_esik}) Pusu iptal.")
                    durum.pusu_iptal.set()
                    return
            await asyncio.sleep(2)
    try:
        asyncio.run(_kontrol())
    except Exception as e:
        print(f"[HATA] Pusu BT kontrol: {e}")

# --- 4. FIREBASE DİNLEYİCİLERİ ---
def uzaktan_komut_dinle():
    popup_sureci = [None]  # Ayrı process referansı

    def komut_callback(event):
        veri = event.data
        if isinstance(veri, dict):
            if veri.get('kilitle') == True:
                print("\n[!] UZAKTAN KİLİTLEME KOMUTU ALINDI!")
                bilgisayari_kilitle()
                db_referans('uzaktan_komut').update({'kilitle': False})
                print("[OK] PC kilitlendi, komut sıfırlandı.")
            
            if veri.get('ses_kapat_ac') == True:
                print("\n[!] KOMUT: Ses Kapat/Aç")
                if PYAUTOGUI_VAR:
                    pyautogui.press('volumemute')
                else:
                    print("[HATA] pyautogui kütüphanesi bulunamadı.")
                db_referans('uzaktan_komut').update({'ses_kapat_ac': False})
                
            if veri.get('ses_arttir') == True:
                print("\n[!] KOMUT: Ses Arttır")
                if PYAUTOGUI_VAR:
                    pyautogui.press('volumeup', presses=2)
                else:
                    print("[HATA] pyautogui kütüphanesi bulunamadı.")
                db_referans('uzaktan_komut').update({'ses_arttir': False})
                
            if veri.get('ses_azalt') == True:
                print("\n[!] KOMUT: Ses Azalt")
                if PYAUTOGUI_VAR:
                    pyautogui.press('volumedown', presses=2)
                else:
                    print("[HATA] pyautogui kütüphanesi bulunamadı.")
                db_referans('uzaktan_komut').update({'ses_azalt': False})

            if veri.get('medya_oynat_durdur') == True:
                print("\n[!] KOMUT: Medya Oynat/Durdur")
                if PYAUTOGUI_VAR:
                    pyautogui.press('playpause')
                else:
                    print("[HATA] pyautogui kütüphanesi bulunamadı.")
                db_referans('uzaktan_komut').update({'medya_oynat_durdur': False})

            if veri.get('uyku') == True:
                print("\n[!] KOMUT: Uyku Modu")
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                db_referans('uzaktan_komut').update({'uyku': False})

            if veri.get('kapat') == True:
                print("\n[!] KOMUT: Bilgisayarı Kapat (15sn geri sayım)")
                
                # Varsa önceki popup'ı zorla kapat
                if popup_sureci[0] is not None:
                    try: popup_sureci[0].terminate()
                    except: pass
                
                db_referans('kapatma_sayac').set({'aktif': True, 'sure': 15})
                
                # Ayrı bir süreç (process) olarak popup'ı başlat (Tkinter thread sorununu %100 çözer)
                python_yolu = sys.executable
                popup_script = os.path.join(ANA_DIZIN, "servis", "kapatma_popup.py")
                popup_sureci[0] = subprocess.Popen([python_yolu, popup_script, "15"])

                def popup_dinle(p):
                    p.wait()  # Sürecin bitmesini bekle
                    
                    # Eğer süreç referansı boşaltılmışsa (mobilden iptal edildiyse) işlem yapma
                    if popup_sureci[0] is not p:
                        return
                        
                    cikis_kodu = p.returncode
                    if cikis_kodu == 0:
                        # Süre doldu
                        print("\n[!!!] SÜRE DOLDU — Bilgisayar kapatılıyor!")
                        db_referans('kapatma_sayac').set({'aktif': False, 'sure': 0})
                        os.system("shutdown /s /t 0")
                    elif cikis_kodu == 1:
                        # Kullanıcı PC'den iptal etti
                        print("\n[!] Kapatma PC'den iptal edildi.")
                        db_referans('kapatma_sayac').set({'aktif': False, 'sure': 0})
                        popup_sureci[0] = None

                threading.Thread(target=popup_dinle, args=(popup_sureci[0],), daemon=True).start()
                db_referans('uzaktan_komut').update({'kapat': False})

            if veri.get('kapatma_iptal') == True:
                print("\n[!] KOMUT: Kapatma Mobilden İptal Edildi")
                if popup_sureci[0] is not None:
                    try: popup_sureci[0].terminate()
                    except: pass
                    popup_sureci[0] = None
                db_referans('kapatma_sayac').set({'aktif': False, 'sure': 0})
                db_referans('uzaktan_komut').update({'kapatma_iptal': False})

    db_referans('uzaktan_komut').listen(komut_callback)

def sistem_ayarlari_dinle():
    """sistem_ayarlari düğümünü dinler: kilit ayarları + dinamik BT adresi tek listener'da."""
    def ayarlar_callback(event):
        v = event.data
        if not isinstance(v, dict): return

        if 'kilit_aktif' in v:
            with durum._lock:
                eski = durum.kilit_aktif
                durum.kilit_aktif = bool(v['kilit_aktif'])
            if eski != durum.kilit_aktif and durum.servis_hazir:
                print(f"\n[AYAR] Güvenlik Sistemi: {'AÇIK' if durum.kilit_aktif else 'KAPALI'}")

        if 'kilit_esik' in v:
            yeni_esik = float(v['kilit_esik'])
            with durum._lock:
                if yeni_esik != durum.kilit_esik:
                    durum.kilit_esik = yeni_esik
                    if durum.servis_hazir:
                        print(f"\n[AYAR] Yeni Sinyal Eşiği: {durum.kilit_esik}")

        # Dinamik BT adresi
        yeni_adres = v.get('hedef_bt_adres', '').upper()
        if yeni_adres:
            with durum._lock:
                if yeni_adres != durum.hedef_adres:
                    durum.hedef_adres = yeni_adres
                    print(f"\n[AYAR] Hedef BT adresi güncellendi: {durum.hedef_adres}")
                    
        # Oto kalibrasyon değişimi dinleme
        if 'oto_kalibrasyon' in v:
            acik = bool(v['oto_kalibrasyon'])
            if acik and durum.servis_hazir:
                print(f"\n[AYAR] Oto Kalibrasyon Mobilden Açıldı. Yeniden hesaplanıyor...")
                def _yeniden_kalibre_et():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    yeni = loop.run_until_complete(kalibrasyon_yap(15))
                    with durum._lock:
                        durum.kilit_esik = yeni
                    # Mobildeki slider'ın da güncellenmesi için Firebase'e geri yaz
                    db_referans('sistem_ayarlari').update({'kilit_esik': yeni})
                threading.Thread(target=_yeniden_kalibre_et, daemon=True).start()

    db_referans('sistem_ayarlari').listen(ayarlar_callback)

# --- OTO KALİBRASYON ---
async def kalibrasyon_yap(sure=15):
    print(f"\n[KALİBRASYON] Lütfen telefonu PC'nin yanına bırakın... ({sure}sn)")
    rssi_degerleri = []
    
    def kalibrasyon_cb(device, adv):
        if device.address.upper() == durum.hedef_adres:
            rssi_degerleri.append(adv.rssi)

    scanner = BleakScanner(detection_callback=kalibrasyon_cb)
    await scanner.start()

    for i in range(sure, 0, -1):
        print(f"Ölçülüyor... Kalan: {i}sn | Alınan Veri: {len(rssi_degerleri)}   ", end="\r")
        await asyncio.sleep(1)

    await scanner.stop()

    if rssi_degerleri:
        ortalama = sum(rssi_degerleri) / len(rssi_degerleri)
        esik = round(ortalama - 30.0, 1) # Güvenli tolerans: -30 dBm
        if esik < -100.0: esik = -100.0
        if esik > -40.0: esik = -40.0
        print(f"\n[OK] Kalibrasyon Bitti! Ortalama Sinyal: {ortalama:.1f} dBm | Belirlenen Eşik: {esik} dBm")
        return esik
    else:
        print("\n[HATA] Telefon bulunamadı! Standart eşik (-75.0) uygulanıyor.")
        return -75.0

# --- 5. ANA DÖNGÜ ---
async def ana_dongu():
    # Sistem tepsisi (System Tray) başlat
    sistem_tepsisi_ikonu_baslat()

    # Servis kapalıyken birikmiş komutları temizle (açılışta eski komutların çalışmasını engelle)
    try:
        db_referans('uzaktan_komut').set({
            'kilitle': False, 'ses_kapat_ac': False, 'ses_arttir': False,
            'ses_azalt': False, 'medya_oynat_durdur': False, 'uyku': False,
            'kapat': False, 'kapatma_iptal': False
        })
        print("[SİSTEM] Bekleyen komutlar temizlendi.")
    except Exception:
        pass

    threading.Thread(target=sistem_bilgilerini_guncelle, args=(db_referans, SISTEM_GUNCELLEME_ARALIGI), daemon=True).start()
    threading.Thread(target=uzaktan_komut_dinle, daemon=True).start()
    threading.Thread(target=sistem_ayarlari_dinle, daemon=True).start()
    print("[SİSTEM] İzleyiciler ve dinleyiciler başlatıldı.")

    # Başlangıçta Firebase'den dinamik BT adresini ve alarm durumunu yükle
    try:
        ilk_veri = db_referans('sistem_ayarlari').get() or {}
        kayitli_adres = ilk_veri.get('hedef_bt_adres', '').upper()
        if kayitli_adres:
            durum.hedef_adres = kayitli_adres
            print(f"[AYAR] Hedef BT adresi: {durum.hedef_adres}")
        else:
            print(f"[AYAR] Varsayılan adres kullanılıyor: {durum.hedef_adres}")
        
        # Kilit durumunu Firebase'den oku (varsayılan False, mobilden açılmadıysa kilitlemesin)
        durum.kilit_aktif = bool(ilk_veri.get('kilit_aktif', False))
        print(f"[AYAR] Kilit durumu: {'AÇIK' if durum.kilit_aktif else 'KAPALI'}")
    except Exception as e:
        print(f"[HATA] Başlangıç ayarları okunamadı: {e}")
        ilk_veri = {}

    # Servis başlarken alarm ekranını sıfırla (önceki oturumdan kalmasın)
    try:
        db_referans('guvenlik_olayi').set({'durum': 'GUVENLI', 'foto': '', 'foto_2': '', 'foto_3': '', 'foto_sayisi': 0})
    except Exception:
        pass

    # Firebase'den oto kalibrasyon ayarını al (yukarıdaki ilk_veri'yi kullan)
    oto_kalibrasyon = ilk_veri.get('oto_kalibrasyon', True)
    
    if oto_kalibrasyon:
        oto_esik = await kalibrasyon_yap()
        durum.kilit_esik = oto_esik
        # Yeni eşiği Firebase'e yazalım ki mobil uygulamadaki Slider kendi kendine oraya kaysın
        try:
            db_referans('sistem_ayarlari').update({'kilit_esik': oto_esik})
        except Exception:
            pass
    else:
        # Oto kapalıysa Firebase'deki mevcut manuel eşiği kullan, yoksa -75 yap
        durum.kilit_esik = ilk_veri.get('kilit_esik', -75.0)
        print(f"\n[!] Oto Kalibrasyon KAPALI. Manuel Eşik ({durum.kilit_esik} dBm) kullanılıyor.")

    print(f"\n[!] Servis Başladı. (Kilit Aktif: {durum.kilit_aktif})")
    bluetooth_durumu_guncelle("KALIBRE_EDILDI", esik=durum.kilit_esik)
    
    # Tüm ayarlar oturdu, log basımı açılabilir
    durum.servis_hazir = True

    while True:
        durum.kilitlendi_mi = False
        durum.zayif_sinyal_kronometresi = 0
        durum.son_gorulme_zamani = time.time()
        durum.rssi_gecmisi.clear()

        scanner = BleakScanner(detection_callback=tarama_callback)
        await scanner.start()

        try:
            while not durum.kilitlendi_mi:
                gecen_sure = time.time() - durum.son_gorulme_zamani

                if not durum.kilit_aktif:
                    print(f"Sistem Devre Dışı (Mobilden kapalı). Son sinyal: {gecen_sure:.1f}sn      ", end="\r")
                    bluetooth_durumu_guncelle("KAPALI", esik=durum.kilit_esik)
                    await asyncio.sleep(1)
                    continue

                if gecen_sure >= SINYAL_KOPMA_SURESI:
                    print(f"\n[KİLİT] Sinyal kaybı! ({gecen_sure:.1f} saniyedir veri yok)")
                    bluetooth_durumu_guncelle("SINYAL_KAYBI")
                    bilgisayari_kilitle()
                    durum.pusu_iptal.clear()
                    threading.Thread(target=fotograf_cek_ve_gonder, args=(db_referans, ANA_DIZIN, durum.pusu_iptal), daemon=True).start()
                    threading.Thread(target=pusu_sirasinda_bt_kontrol, daemon=True).start()
                    durum.kilitlendi_mi = True
                    break

                if len(durum.rssi_gecmisi) > 0:
                    ortalama = sum(durum.rssi_gecmisi) / len(durum.rssi_gecmisi)
                    if ortalama < durum.kilit_esik:
                        durum.zayif_sinyal_kronometresi += 1
                        durum_str = "!!! KRİTİK !!!"
                        bluetooth_durumu_guncelle("KRITIK", rssi=ortalama, esik=durum.kilit_esik)
                    else:
                        durum.zayif_sinyal_kronometresi = 0
                        durum_str = "GÜVENLİ"
                        bluetooth_durumu_guncelle("BAGLI", rssi=ortalama, esik=durum.kilit_esik)

                    if durum.zayif_sinyal_kronometresi >= ONAY_SURESI:
                        print(f"\n[KİLİT] Zayıf sinyal zaman aşımı!")
                        bluetooth_durumu_guncelle("ZAYIF_SINYAL_KILIDI")
                        bilgisayari_kilitle()
                        durum.pusu_iptal.clear()
                        threading.Thread(target=fotograf_cek_ve_gonder, args=(db_referans, ANA_DIZIN, durum.pusu_iptal), daemon=True).start()
                        threading.Thread(target=pusu_sirasinda_bt_kontrol, daemon=True).start()
                        durum.kilitlendi_mi = True
                    else:
                        print(f"{durum_str} | RSSI: {ortalama:.1f} | Eşik: {durum.kilit_esik} | Sayaç: {durum.zayif_sinyal_kronometresi}sn | Son: {gecen_sure:.1f}sn    ", end="\r", flush=True)
                else:
                    print(f"Telefon aranıyor... ({gecen_sure:.1f}sn oldu)    ", end="\r", flush=True)
                    bluetooth_durumu_guncelle("ARANIYOR", esik=durum.kilit_esik)

                await asyncio.sleep(1)
        finally:
            await scanner.stop()

        if durum.kilitlendi_mi:
            print("\n[YENİDEN BAŞLAMA] 30 saniye bekleniyor...")
            bluetooth_durumu_guncelle("BEKLENIYOR", zorla=True)
            await asyncio.sleep(30)
            print("[YENİDEN BAŞLAMA] Tarama yeniden başlatılıyor...\n")

if __name__ == "__main__":
    import traceback
    import logging

    # pythonw.exe hataları sessizce yutar — dosyaya loglayalım
    os.makedirs(os.path.join(ANA_DIZIN, "logs"), exist_ok=True)
    hata_log = os.path.join(ANA_DIZIN, "logs", "servis_hata_log.txt")
    logging.basicConfig(
        filename=hata_log,
        level=logging.ERROR,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8"
    )

    try:
        asyncio.run(ana_dongu())
    except KeyboardInterrupt:
        print("\n[!] Durduruldu. Firebase'e kapanış durumu yazılıyor...")
        try:
            bluetooth_durumu_guncelle("KAPALI", zorla=True)
        except Exception:
            pass
        print("[OK] Servis kapatıldı.")
    except Exception as e:
        logging.error(f"Servis çöktü!\n{traceback.format_exc()}")
        # Tekrar dene (ağ gecikmesi olabilir)
        import time as _time
        _time.sleep(10)
        try:
            asyncio.run(ana_dongu())
        except Exception as e2:
            logging.error(f"Yeniden deneme de başarısız!\n{traceback.format_exc()}")