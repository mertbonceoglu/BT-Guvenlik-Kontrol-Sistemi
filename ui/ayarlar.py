import flet as ft
import threading
from core.firebase_baglanti import db_referans
from core.config import FIREBASE_PROJE, UYGULAMA_VERSIYON
from ui.bilesenler import cam_kutu

# Bleak sadece PC'de var
try:
    from bleak import BleakScanner
    BLEAK_VAR = True
except ImportError:
    BLEAK_VAR = False

class AyarlarSekmesi(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.app_page = page
        self.expand = True
        self.padding = ft.Padding.only(left=16, right=16, top=44, bottom=8)
        
        # --- UI Elemanları ---
        self.toplam_alarm_metin = ft.Text("Hesaplanıyor...", size=12, color=ft.Colors.WHITE54)
        self.firebase_durum_metin = ft.Text("Bağlı ✅", size=12, color=ft.Colors.GREEN_ACCENT_200)
        
        # Mevcut BT hedef adresi (Firebase'den okunur)
        self.bt_adres_metin = ft.Text("Yükleniyor...", size=13, color=ft.Colors.CYAN_ACCENT_200)
        
        # BT tarama sonuçları listesi
        self.tarama_sonuclari = ft.Column(spacing=6, controls=[])
        self.tarama_yukleniyor = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)
        self.tarama_butonu = ft.ElevatedButton(
            "Cihaz Tara",
            icon=ft.Icons.BLUETOOTH_SEARCHING,
            on_click=self.bt_tara,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.CYAN_900,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            disabled=not BLEAK_VAR
        )

        self.oto_kalibre_switch = ft.Switch(
            label="Otomatik Kalibrasyon Modu (15sn)",
            value=True,
            active_color=ft.Colors.GREEN_ACCENT_200,
            on_change=self.oto_kalibre_degisti
        )
        
        self.esik_slider = ft.Slider(
            min=-100, max=-40, divisions=60, 
            label="{value} dBm", value=-75,
            active_color=ft.Colors.CYAN_ACCENT_200,
            disabled=True,
            on_change_end=self.esik_degisti
        )

        self.content = self.arayuzu_olustur()
        
        # --- Firebase Dinleyicileri ---
        db_referans('sistem_ayarlari').listen(self.ayar_cb)
        # Mevcut BT adresini Firebase'den yükle
        self._bt_adres_yukle()

    def _bt_adres_yukle(self):
        try:
            veri = db_referans('sistem_ayarlari').get() or {}
            adres = veri.get('hedef_bt_adres', 'Ayarlanmadı')
            self.bt_adres_metin.value = adres
        except Exception:
            pass

    def arayuzu_olustur(self):
        return ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Text("Ayarlar", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                
                # --- Bluetooth Cihaz Eşleştirme ---
                cam_kutu(
                    icerik=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("Bluetooth Cihaz Eşleştirme", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE70),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(spacing=2, controls=[
                                        ft.Text("Aktif Hedef Cihaz", size=12, color=ft.Colors.WHITE38),
                                        self.bt_adres_metin,
                                    ]),
                                    ft.Row(controls=[self.tarama_yukleniyor, self.tarama_butonu]) if BLEAK_VAR else ft.Container(),
                                ]
                            ),
                            ft.Text(
                                "Etraftaki cihazları tara, listeden telefonunu seç." if BLEAK_VAR else "Eşleştirme işlemini bilgisayarınız üzerinden yapınız.\nPC'de main.py açarak Ayarlar > Cihaz Tara ile yeni telefon ekleyebilirsiniz.",
                                size=11, color=ft.Colors.AMBER_200 if not BLEAK_VAR else ft.Colors.WHITE38
                            ),
                            self.tarama_sonuclari,
                        ],
                    )
                ),
                
                # --- Mesafe / Sinyal Ayarı ---
                cam_kutu(
                    icerik=ft.Column(
                        spacing=8,
                        controls=[
                            self.oto_kalibre_switch,
                            ft.Divider(color=ft.Colors.WHITE12, height=1),
                            ft.Text("Manuel Mesafe Kalibrasyonu (Sinyal Eşiği)", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE70),
                            ft.Text("Daha eksi değerler (-90 gibi) daha uzağa gidince kilitler.", size=11, color=ft.Colors.WHITE38),
                            self.esik_slider,
                        ],
                    )
                ),
                
                # --- Cihaz Bilgileri ---
                cam_kutu(
                    icerik=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("Sistem Bilgileri", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE70),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                                ft.Text("Firebase Proje", size=13, color=ft.Colors.WHITE54),
                                ft.Text(FIREBASE_PROJE, size=13, color=ft.Colors.CYAN_ACCENT_200),
                            ]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                                ft.Text("Firebase Durumu", size=13, color=ft.Colors.WHITE54),
                                self.firebase_durum_metin,
                            ]),
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                                ft.Text("Toplam Alarm", size=13, color=ft.Colors.WHITE54),
                                self.toplam_alarm_metin,
                            ]),
                        ],
                    )
                ),
                
                # --- Hakkında ---
                cam_kutu(
                    icerik=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Hakkında", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE70),
                            ft.Text("ProxiGuard: Bluetooth Tabanlı Güvenlik ve Kontrol Sistemi", size=12, color=ft.Colors.WHITE38),
                            ft.Text("Bluetooth RSSI Tabanlı Akıllı Kilitleme", size=12, color=ft.Colors.WHITE38),
                            ft.Text(f"Flet {ft.__version__} • Firebase RTDB", size=12, color=ft.Colors.WHITE38),
                        ],
                    )
                ),
            ],
        )

    def bt_tara(self, e):
        """Etraftaki Bluetooth cihazlarını tarar ve listeler."""
        if not BLEAK_VAR:
            return
        self.tarama_butonu.disabled = True
        self.tarama_yukleniyor.visible = True
        self.tarama_sonuclari.controls.clear()
        self.tarama_sonuclari.controls.append(
            ft.Text("Taranıyor... (10 saniye)", size=12, color=ft.Colors.WHITE54, italic=True)
        )
        self.app_page.update()

        def _tara():
            import asyncio
            bulunan = {}

            async def _async_tara():
                def cb(device, adv):
                    if device.address not in bulunan:
                        bulunan[device.address] = device.name or "İsimsiz Cihaz"

                scanner = BleakScanner(detection_callback=cb)
                await scanner.start()
                await asyncio.sleep(10)
                await scanner.stop()

            asyncio.run(_async_tara())

            self.tarama_sonuclari.controls.clear()
            if bulunan:
                self.tarama_sonuclari.controls.append(
                    ft.Text(f"{len(bulunan)} cihaz bulundu — birini seç:", size=12, color=ft.Colors.WHITE54)
                )
                for adres, isim in bulunan.items():
                    a, i = adres, isim  # closure için kopyala
                    self.tarama_sonuclari.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.BLUETOOTH, color=ft.Colors.CYAN_ACCENT_200, size=18),
                            title=ft.Text(i, size=13, color=ft.Colors.WHITE),
                            subtitle=ft.Text(a, size=11, color=ft.Colors.WHITE38),
                            on_click=lambda e, adres=a, isim=i: self._cihaz_sec(adres, isim),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        )
                    )
            else:
                self.tarama_sonuclari.controls.append(
                    ft.Text("Cihaz bulunamadı. Telefonunuzun Bluetooth'u açık mı?", size=12, color=ft.Colors.RED_300)
                )

            self.tarama_butonu.disabled = False
            self.tarama_yukleniyor.visible = False
            self.app_page.update()

        threading.Thread(target=_tara, daemon=True).start()

    def _cihaz_sec(self, adres, isim):
        """Seçilen cihazı Firebase'e kaydeder."""
        try:
            db_referans('sistem_ayarlari').update({'hedef_bt_adres': adres.upper()})
            self.bt_adres_metin.value = adres.upper()
            self.tarama_sonuclari.controls.clear()
            self.app_page.snack_bar = ft.SnackBar(
                content=ft.Text(f"{isim} ({adres.upper()}) hedef olarak ayarlandı! PC servisini yeniden başlatın."),
                bgcolor=ft.Colors.GREEN_900, duration=4000
            )
            self.app_page.snack_bar.open = True
            self.app_page.update()
        except Exception as ex:
            print(f"[HATA] Cihaz kaydedilemedi: {ex}")

    def oto_kalibre_degisti(self, e):
        self.esik_slider.disabled = self.oto_kalibre_switch.value
        try:
            db_referans('sistem_ayarlari').update({'oto_kalibrasyon': self.oto_kalibre_switch.value})
            durum = "AKTİF. PC servisi başlatılırken otomatik ölçecek." if self.oto_kalibre_switch.value else "KAPALI. Slider üzerinden manuel değer verebilirsiniz."
            self.app_page.snack_bar = ft.SnackBar(content=ft.Text(f"Oto Kalibrasyon: {durum}"), bgcolor=ft.Colors.GREEN_900)
            self.app_page.snack_bar.open = True
            if self.page:
                self.app_page.update()
        except Exception:
            pass

    def esik_degisti(self, e):
        try:
            db_referans('sistem_ayarlari').update({'kilit_esik': self.esik_slider.value})
            self.app_page.snack_bar = ft.SnackBar(content=ft.Text(f"Sinyal kilitleme eşiği manuel {self.esik_slider.value} dBm olarak ayarlandı."), bgcolor=ft.Colors.GREEN_900)
            self.app_page.snack_bar.open = True
            self.app_page.update()
        except Exception:
            pass

    def ayar_cb(self, event):
        v = event.data
        if not isinstance(v, dict): return
        try:
            if 'oto_kalibrasyon' in v:
                self.oto_kalibre_switch.value = bool(v['oto_kalibrasyon'])
                self.esik_slider.disabled = self.oto_kalibre_switch.value
            if 'kilit_esik' in v:
                self.esik_slider.value = float(v['kilit_esik'])
            if 'hedef_bt_adres' in v:
                self.bt_adres_metin.value = v['hedef_bt_adres']
            if self.page:
                self.app_page.update()
        except Exception:
            pass

    def set_toplam_alarm(self, sayi):
        """Geçmiş sekmesinden çağrılarak toplam alarm sayısını günceller."""
        self.toplam_alarm_metin.value = str(sayi)
        try:
            if self.page:
                self.app_page.update()
        except Exception:
            pass
