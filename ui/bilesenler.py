import flet as ft
import os
import time
import shutil

# BT durum kodlarını Türkçe'ye çeviren sözlük
BT_DURUM_CEVIRI = {
    'BAGLI': '📡 Bağlı',
    'KRITIK': '⚠️ Kritik',
    'ARANIYOR': '🔍 Aranıyor',
    'SINYAL_KAYBI': '❌ Sinyal Kayıp',
    'KALIBRE_EDILDI': '📐 Kalibre Edildi',
    'ZAYIF_SINYAL_KILIDI': '🔒 Zayıf Sinyal Kilidi',
    'BEKLENIYOR': '⏳ Bekleniyor',
    'KAPALI': '⛔ Servis Kapalı',
}

BT_DURUM_RENK = {
    'BAGLI': ft.Colors.GREEN_ACCENT_200,
    'KRITIK': ft.Colors.RED_ACCENT_200,
    'ARANIYOR': ft.Colors.AMBER,
    'SINYAL_KAYBI': ft.Colors.RED,
    'KALIBRE_EDILDI': ft.Colors.CYAN_ACCENT_200,
    'ZAYIF_SINYAL_KILIDI': ft.Colors.RED,
    'BEKLENIYOR': ft.Colors.AMBER,
    'KAPALI': ft.Colors.WHITE38,
}

def bilgi_karti(icon_name, baslik, deger_ref, renk, genislik=155, expand=False, ring_ref=None):
    """Dashboard için glassmorphism tarzı bilgi kartı oluşturur."""
    
    # Progress ring varsa icon'u stack içine al
    if ring_ref:
        icon_or_ring = ft.Stack(
            controls=[
                ring_ref,
                ft.Container(content=ft.Icon(icon_name, color=renk, size=16), width=32, height=32, alignment=ft.Alignment(0, 0))
            ]
        )
    else:
        icon_or_ring = ft.Icon(icon_name, color=renk, size=20)

    return ft.Container(
        width=genislik if not expand else None,
        expand=expand,
        height=100,
        border_radius=16,
        bgcolor=ft.Colors.with_opacity(0.08, renk),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, renk)),
        padding=ft.Padding.all(8),
        content=ft.Column(
            spacing=4,
            controls=[
                icon_or_ring,
                ft.Text(baslik, size=10, color=ft.Colors.WHITE54),
                deger_ref,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

def cam_kutu(icerik, renk=ft.Colors.WHITE):
    """Ortak cam (glassmorphism) paneli oluşturur."""
    return ft.Container(
        border_radius=16, padding=ft.Padding.all(16),
        bgcolor=ft.Colors.with_opacity(0.06, renk),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, renk)),
        content=icerik
    )

def snackbar_goster(page, mesaj, renk=ft.Colors.GREEN_900):
    """SnackBar gösterir."""
    sb = ft.SnackBar(content=ft.Text(mesaj), bgcolor=renk, duration=3000)
    page.snack_bar = sb
    page.snack_bar.open = True
    page.update()

def foto_kaydet(kaynak_yol, page):
    """Fotoğrafı Downloads klasörüne kaydeder. Hem Android hem Windows uyumlu."""
    print(f"[KAYIT] foto_kaydet cagirildi, yol: {kaynak_yol}")
    if not kaynak_yol:
        snackbar_goster(page, "Kaydedilecek fotoğraf yok.", ft.Colors.RED_900)
        return
    try:
        if os.name == 'nt':
            # Windows ortamı (Masaüstü uygulaması testi)
            indirme = os.path.join(os.path.expanduser('~'), 'Downloads', 'ProxiGuard')
            os.makedirs(indirme, exist_ok=True)
        else:
            # Android ortamı
            indirme = '/storage/emulated/0/Download/ProxiGuard'
            try:
                os.makedirs(indirme, exist_ok=True)
            except Exception:
                # Klasör oluşturma izni yoksa (Android 11+ Scoped Storage) doğrudan Download ana dizinine at
                indirme = '/storage/emulated/0/Download'

        # Üst üste binmeyi engellemek için milisaniye bazında isimlendirme
        dosya_adi = f"mudahale_{int(time.time() * 1000)}.jpg"
        hedef = os.path.join(indirme, dosya_adi)
        shutil.copy2(kaynak_yol, hedef)
        print(f"[KAYIT] Basariyla kaydedildi: {hedef}")
        
        gosterilecek_isim = f"ProxiGuard/{dosya_adi}" if "ProxiGuard" in indirme else dosya_adi
        snackbar_goster(page, f"Kaydedildi: {gosterilecek_isim}")
    except Exception as ex:
        print(f"[KAYIT HATA] {ex}")
        snackbar_goster(page, f"Kaydetme hatasi: {ex}", ft.Colors.RED_900)

