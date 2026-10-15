import psutil
import os
import time

def sistem_bilgilerini_guncelle(db_referans, guncelleme_araligi=5):
    """CPU, RAM, Batarya, Disk bilgilerini belirli aralıklarla Firebase'e gönderir."""

    while True:
        try:
            bilgi = {
                'cpu_yuzde': psutil.cpu_percent(interval=1),
                'ram_yuzde': psutil.virtual_memory().percent,
                'disk_kullanim': psutil.disk_usage(os.environ.get('SystemDrive', 'C:\\')).percent,
                'son_guncelleme': time.strftime("%Y-%m-%d %H:%M:%S")
            }

            batarya = psutil.sensors_battery()
            if batarya:
                bilgi['batarya_yuzde'] = batarya.percent
                bilgi['batarya_sarjda'] = batarya.power_plugged
            else:
                bilgi['batarya_yuzde'] = -1
                bilgi['batarya_sarjda'] = False

            try:
                db_referans('sistem_durumu').set(bilgi)
            except Exception:
                pass
        except Exception as e:
            print(f"[HATA] Sistem bilgisi okunamadı: {e}")

        time.sleep(guncelleme_araligi)

