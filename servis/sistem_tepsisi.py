import threading
import os

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_VAR = True
except ImportError:
    PYSTRAY_VAR = False

def _create_image():
    """Tepsi ikonu için uygulamanın kendi icon.png dosyasını kullanır."""
    try:
        # ANA_DIZIN'i bularak assets/icon.png yolunu oluştur
        ana_dizin = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ikon_yolu = os.path.join(ana_dizin, "assets", "icon.png")
        if os.path.exists(ikon_yolu):
            return Image.open(ikon_yolu)
    except Exception:
        pass
        
    # Eğer icon.png bulunamazsa veya yüklenemezse fallback (yedek) olarak basit bir kare çiz
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill=(0, 255, 128))
    return image

def _tepsi_baslat():
    """Tepsi ikonunu çalıştırır."""
    if not PYSTRAY_VAR:
        return

    def on_quit(icon, item):
        print("\n[!] Sistem tepsisinden çıkış yapıldı.")
        try:
            from core.firebase_baglanti import db_referans
            import time
            db_referans('bluetooth').set({
                'durum': 'KAPALI',
                'son_gorulme': time.strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception:
            pass
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("ProxiGuard - Çıkış", on_quit)
    )
    icon = pystray.Icon("ProxiGuard", _create_image(), "ProxiGuard Servisi", menu=menu)
    icon.run()

def sistem_tepsisi_ikonu_baslat():
    """Tepsi ikonunu arka planda başlatır (Windows uyumlu)."""
    if PYSTRAY_VAR:
        threading.Thread(target=_tepsi_baslat, daemon=True).start()
