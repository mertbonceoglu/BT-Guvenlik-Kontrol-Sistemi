import flet as ft
import asyncio
try:
    import psutil
    PSUTIL_VAR = True
except ImportError:
    PSUTIL_VAR = False
import os
import time
from datetime import datetime
from core.firebase_baglanti import db_referans
from ui.bilesenler import bilgi_karti, cam_kutu, BT_DURUM_CEVIRI, BT_DURUM_RENK

class DashboardSekmesi(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.app_page = page
        self.expand = True
        self.padding = ft.Padding.only(left=16, right=16, top=44, bottom=8)
        
        # --- UI Elemanlari ---
        self.bt_durum_metin = ft.Text("Baglanıyor...", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
        self.bt_rssi_metin = ft.Text("--", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT_200)
        self.bt_esik_metin = ft.Text("--", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE54)
        
        self.servis_durum_ikon = ft.Container(width=10, height=10, border_radius=5, bgcolor=ft.Colors.RED)
        self.servis_durum_metin = ft.Text("Servis: Cevrimdisi", size=12, color=ft.Colors.WHITE38)
        
        self.guvenlik_switch = ft.Switch(
            label="Guvenlik Kilit Sistemi", 
            value=True, 
            active_color=ft.Colors.GREEN_ACCENT_200,
            on_change=self.kilit_durum_degisti
        )
        
        self.cpu_deger = ft.Text("--%", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_ACCENT_200)
        self.cpu_ring = ft.ProgressRing(value=0, width=32, height=32, stroke_width=3, color=ft.Colors.BLUE_ACCENT_200, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_ACCENT_200))
        
        self.ram_deger = ft.Text("--%", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_ACCENT_200)
        self.ram_ring = ft.ProgressRing(value=0, width=32, height=32, stroke_width=3, color=ft.Colors.PURPLE_ACCENT_200, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.PURPLE_ACCENT_200))
        
        self.batarya_deger = ft.Text("--%", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_ACCENT_200)
        self.batarya_ring = ft.ProgressRing(value=0, width=32, height=32, stroke_width=3, color=ft.Colors.GREEN_ACCENT_200, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN_ACCENT_200))
        
        self.disk_deger = ft.Text("--%", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_ACCENT_200)
        self.disk_ring = ft.ProgressRing(value=0, width=32, height=32, stroke_width=3, color=ft.Colors.ORANGE_ACCENT_200, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ORANGE_ACCENT_200))
        
        self.son_guncelleme = ft.Text("", size=11, color=ft.Colors.WHITE38)
        self.son_bt_zamani = 0
        self._guncelleme_basladi = False
        
        self._kapatma_iptal_icon = ft.IconButton(
            icon=ft.Icons.CANCEL_OUTLINED, 
            tooltip="Kapatmayı İptal Et", 
            icon_color=ft.Colors.WHITE38, 
            disabled=True,
            on_click=lambda e: self.komut_gonder('kapatma_iptal')
        )
        self._kapatma_iptal_text = ft.Text("Kapatma İptal", size=10, color=ft.Colors.WHITE38, text_align=ft.TextAlign.CENTER)

        self.kapatma_iptal_btn = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
            controls=[
                self._kapatma_iptal_icon,
                self._kapatma_iptal_text
            ]
        )

        self.guvenlik_paneli = ft.Container(
            border_radius=16, padding=ft.Padding.all(16),
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            animate=ft.Animation(duration=500),
            content=ft.Column(
                spacing=12,
                controls=[
                    self.guvenlik_switch,
                    ft.Divider(color=ft.Colors.WHITE12, height=1),
                    ft.Row(controls=[
                        ft.Icon(ft.Icons.BLUETOOTH, color=ft.Colors.BLUE_ACCENT_200, size=20),
                        ft.Text("Bluetooth Baglantisi", size=15, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                    ]),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(spacing=2, controls=[ft.Text("Durum", size=11, color=ft.Colors.WHITE38), self.bt_durum_metin]),
                            ft.Column(spacing=2, controls=[ft.Text("RSSI", size=11, color=ft.Colors.WHITE38), self.bt_rssi_metin]),
                            ft.Column(spacing=2, controls=[ft.Text("Esik", size=11, color=ft.Colors.WHITE38), self.bt_esik_metin]),
                        ],
                    ),
                ],
            ),
        )

        self.content = self.arayuzu_olustur()
        
        # --- Firebase Dinleyicileri ---
        db_referans('bluetooth').listen(self.bt_cb)
        db_referans('sistem_ayarlari').listen(self.ayar_cb)
        db_referans('kapatma_sayac').listen(self.kapatma_sayac_cb)
        if not PSUTIL_VAR:
            db_referans('sistem_durumu').listen(self.sistem_cb)
        
    def kapatma_sayac_cb(self, event):
        v = event.data
        aktif = False
        if isinstance(v, dict):
            aktif = v.get('aktif', False)
            
        degisim_var = False
        if aktif and self._kapatma_iptal_icon.disabled:
            self._kapatma_iptal_icon.disabled = False
            self._kapatma_iptal_icon.icon_color = ft.Colors.AMBER_400
            self._kapatma_iptal_text.color = ft.Colors.WHITE54
            degisim_var = True
        elif not aktif and not self._kapatma_iptal_icon.disabled:
            self._kapatma_iptal_icon.disabled = True
            self._kapatma_iptal_icon.icon_color = ft.Colors.WHITE38
            self._kapatma_iptal_text.color = ft.Colors.WHITE38
            degisim_var = True
            
        if degisim_var:
            try:
                self.app_page.update()
            except Exception:
                pass
        
        if not self._guncelleme_basladi:
            self._guncelleme_basladi = True
            self.app_page.run_task(self.periyodik_sistem_guncelleme)

    def arayuzu_olustur(self):
        return ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(spacing=10, controls=[
                            ft.Image(src="assets/icon.png", width=36, height=36, border_radius=8),
                            ft.Text("Dashboard", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ]),
                        ft.Row(spacing=6, controls=[self.servis_durum_ikon, self.servis_durum_metin]),
                    ],
                ),
                self.guvenlik_paneli,
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Sistem Bilgileri", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE70),
                                self.son_guncelleme
                            ]
                        ),
                        ft.Row(
                            wrap=False, spacing=6,
                            controls=[
                                bilgi_karti(ft.Icons.MEMORY, "CPU", self.cpu_deger, ft.Colors.BLUE_ACCENT_200, expand=True, ring_ref=self.cpu_ring),
                                bilgi_karti(ft.Icons.STORAGE, "RAM", self.ram_deger, ft.Colors.PURPLE_ACCENT_200, expand=True, ring_ref=self.ram_ring),
                                bilgi_karti(ft.Icons.BATTERY_CHARGING_FULL, "Batarya", self.batarya_deger, ft.Colors.GREEN_ACCENT_200, expand=True, ring_ref=self.batarya_ring),
                                bilgi_karti(ft.Icons.DISC_FULL, "Disk", self.disk_deger, ft.Colors.ORANGE_ACCENT_200, expand=True, ring_ref=self.disk_ring),
                            ],
                        ),
                    ]
                ),
                
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text("Güç ve Güvenlik Kontrolleri", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE70),
                        cam_kutu(
                            renk=ft.Colors.RED,
                            icerik=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                controls=[
                                    ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.IconButton(icon=ft.Icons.LOCK, tooltip="Bilgisayarı Kilitle", icon_color=ft.Colors.RED_ACCENT_200, on_click=lambda e: self.komut_gonder('kilitle')),
                                        ft.Text("Kilitle", size=10, color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER)
                                    ]),
                                    ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.IconButton(icon=ft.Icons.BEDTIME, tooltip="Uyku Modu", icon_color=ft.Colors.AMBER_400, on_click=lambda e: self.islem_onayi_goster("Uyku Modu", "Bilgisayarı uyku moduna almak istediğinize emin misiniz?", "Evet, Uyut", "uyku", ft.Colors.AMBER_400)),
                                        ft.Text("Uyku", size=10, color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER)
                                    ]),
                                    ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.IconButton(icon=ft.Icons.POWER_SETTINGS_NEW, tooltip="Bilgisayarı Kapat", icon_color=ft.Colors.RED_ACCENT_200, on_click=lambda e: self.islem_onayi_goster("Bilgisayarı Kapat", "Bilgisayarı kapatmak istediğinize emin misiniz?\n\nOnayladığınızda bilgisayarda 15 saniyelik bir geri sayım başlayacaktır.", "Evet, Kapat (15sn)", "kapat", ft.Colors.RED_ACCENT_200)),
                                        ft.Text("Kapat", size=10, color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER)
                                    ]),
                                    self.kapatma_iptal_btn,
                                ]
                            )
                        ),
                    ]
                ),
                
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text("Medya Kontrolleri", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE70),
                        cam_kutu(
                            renk=ft.Colors.BLUE,
                            icerik=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                controls=[
                                    ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.IconButton(icon=ft.Icons.VOLUME_OFF, tooltip="Sesi Kapat", icon_color=ft.Colors.WHITE, on_click=lambda e: self.komut_gonder('ses_kapat_ac')),
                                        ft.Text("Sessiz", size=10, color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER)
                                    ]),
                                    ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.IconButton(icon=ft.Icons.VOLUME_DOWN, tooltip="Sesi Azalt", icon_color=ft.Colors.WHITE, on_click=lambda e: self.komut_gonder('ses_azalt')),
                                        ft.Text("Ses Azalt", size=10, color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER)
                                    ]),
                                    ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.IconButton(icon=ft.Icons.VOLUME_UP, tooltip="Sesi Arttır", icon_color=ft.Colors.WHITE, on_click=lambda e: self.komut_gonder('ses_arttir')),
                                        ft.Text("Ses Arttır", size=10, color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER)
                                    ]),
                                    ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                                        ft.IconButton(icon=ft.Icons.PLAY_CIRCLE_FILLED, tooltip="Oynat/Durdur", icon_color=ft.Colors.WHITE, on_click=lambda e: self.komut_gonder('medya_oynat_durdur')),
                                        ft.Text("Durdur/Oynat", size=10, color=ft.Colors.WHITE54, text_align=ft.TextAlign.CENTER)
                                    ]),
                                ]
                            )
                        ),
                    ]
                ),
            ],
        )

    def islem_onayi_goster(self, baslik, icerik, buton_metni, komut, renk):
        def onay_evet(e2):
            dlg.open = False
            self.app_page.update()
            self.komut_gonder(komut)
            
        def onay_hayir(e2):
            dlg.open = False
            self.app_page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(baslik, color=renk),
            content=ft.Text(icerik),
            actions=[
                ft.TextButton("İptal", on_click=onay_hayir),
                ft.TextButton(buton_metni, on_click=onay_evet, style=ft.ButtonStyle(color=renk)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        try:
            self.app_page.open(dlg)
        except (AttributeError, TypeError):
            if dlg not in self.app_page.overlay:
                self.app_page.overlay.append(dlg)
            dlg.open = True
            self.app_page.update()

    def komut_gonder(self, komut):
        try:
            db_referans('uzaktan_komut').update({komut: True})
            if hasattr(self.app_page, 'snack_bar') and self.app_page.snack_bar:
                self.app_page.snack_bar.content = ft.Text(f"Komut gönderildi: {komut.replace('_', ' ').upper()}")
                self.app_page.snack_bar.open = True
            else:
                self.app_page.snack_bar = ft.SnackBar(content=ft.Text(f"Komut gönderildi: {komut.replace('_', ' ').upper()}"), bgcolor=ft.Colors.GREEN_900)
                self.app_page.snack_bar.open = True
            self.app_page.update()
        except Exception as e:
            print(f"[HATA] Komut gönderilemedi: {e}")

    def kilit_durum_degisti(self, e):
        try:
            db_referans('sistem_ayarlari').update({'kilit_aktif': self.guvenlik_switch.value})
        except Exception:
            pass

    async def periyodik_sistem_guncelleme(self):
        """Her 3 saniyede bir sistem bilgilerini gunceller."""
        while True:
            try:
                if PSUTIL_VAR:
                    cpu = psutil.cpu_percent()
                    ram = psutil.virtual_memory().percent
                    disk = psutil.disk_usage(os.environ.get('SystemDrive', 'C:\\')).percent
                    
                    self.cpu_deger.value = f"{cpu}%"
                    self.cpu_ring.value = cpu / 100.0
                    
                    self.ram_deger.value = f"{ram}%"
                    self.ram_ring.value = ram / 100.0
                    
                    self.disk_deger.value = f"{disk}%"
                    self.disk_ring.value = disk / 100.0
                    
                    batarya = psutil.sensors_battery()
                    if batarya:
                        self.batarya_deger.value = f"{batarya.percent}%"
                        self.batarya_ring.value = batarya.percent / 100.0
                    else:
                        self.batarya_deger.value = "N/A"
                        self.batarya_ring.value = 0
                
                self.son_guncelleme.value = f"Son guncelleme: {datetime.now().strftime('%H:%M:%S')}"
                
                # Servis timeout kontrolu: 15sn'den fazla BT guncellemesi gelmezse uyar
                if self.son_bt_zamani > 0 and (time.time() - self.son_bt_zamani) > 15:
                    self.servis_durum_ikon.bgcolor = ft.Colors.AMBER
                    self.servis_durum_metin.value = "Servis: Yanit Yok"
                    self.servis_durum_metin.color = ft.Colors.AMBER
                
                self.app_page.update()
            except Exception:
                pass
            await asyncio.sleep(3)

    def sistem_cb(self, event):
        v = event.data
        if not isinstance(v, dict): return
        try:
            self.cpu_deger.value = f"{v.get('cpu_yuzde', '--')}%"
            if v.get('cpu_yuzde') is not None and isinstance(v.get('cpu_yuzde'), (int, float)): self.cpu_ring.value = float(v['cpu_yuzde']) / 100.0
            
            self.ram_deger.value = f"{v.get('ram_yuzde', '--')}%"
            if v.get('ram_yuzde') is not None and isinstance(v.get('ram_yuzde'), (int, float)): self.ram_ring.value = float(v['ram_yuzde']) / 100.0
            
            self.disk_deger.value = f"{v.get('disk_kullanim', '--')}%"
            if v.get('disk_kullanim') is not None and isinstance(v.get('disk_kullanim'), (int, float)): self.disk_ring.value = float(v['disk_kullanim']) / 100.0
            
            bat = v.get('batarya_yuzde', -1)
            if bat >= 0:
                self.batarya_deger.value = f"{bat}%"
                self.batarya_ring.value = float(bat) / 100.0
            else:
                self.batarya_deger.value = "N/A"
                self.batarya_ring.value = 0
            self.app_page.update()
        except Exception:
            pass

    def bt_cb(self, event):
        v = event.data
        if not isinstance(v, dict): return
        self.son_bt_zamani = time.time()
        try:
            d = v.get('durum', 'BILINMIYOR')
            self.bt_durum_metin.value = BT_DURUM_CEVIRI.get(d, d)
            self.bt_durum_metin.color = BT_DURUM_RENK.get(d, ft.Colors.AMBER)
            rssi = v.get('rssi')
            self.bt_rssi_metin.value = f"{rssi} dBm" if rssi else "--"
            esik = v.get('esik')
            self.bt_esik_metin.value = f"{esik} dBm" if esik else "--"

            if d == 'KAPALI':
                self.servis_durum_ikon.bgcolor = ft.Colors.RED
                self.servis_durum_metin.value = "Servis: Kapali"
                self.servis_durum_metin.color = ft.Colors.RED_ACCENT_200
                self.son_bt_zamani = 0
            else:
                self.servis_durum_ikon.bgcolor = ft.Colors.GREEN_ACCENT_200
                self.servis_durum_metin.value = "Servis: Aktif"
                self.servis_durum_metin.color = ft.Colors.GREEN_ACCENT_200

            if d in ['SINYAL_KAYBI', 'ZAYIF_SINYAL_KILIDI']:
                self.guvenlik_paneli.border = ft.Border.all(2, ft.Colors.with_opacity(0.8, ft.Colors.RED))
                self.guvenlik_paneli.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.RED)
            else:
                self.guvenlik_paneli.border = ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))
                self.guvenlik_paneli.bgcolor = ft.Colors.with_opacity(0.06, ft.Colors.WHITE)

            try:
                if self.page:
                    self.app_page.update()
            except Exception:
                pass
        except Exception as e:
            print(f"[HATA] DashboardSekmesi.bt_cb: {e}")

    def ayar_cb(self, event):
        v = event.data
        if not isinstance(v, dict): return
        try:
            if 'kilit_aktif' in v:
                self.guvenlik_switch.value = bool(v['kilit_aktif'])
                if self.page:
                    self.app_page.update()
        except Exception:
            pass
