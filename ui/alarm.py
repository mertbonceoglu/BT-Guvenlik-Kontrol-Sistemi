import flet as ft
import base64
import os
import sys
import tempfile
import time
from core.firebase_baglanti import db_referans
from ui.bilesenler import foto_kaydet

# Android'de shutil/tempfile kaydetme çalışmaz
PC_ORTAMI = sys.platform in ('win32', 'linux', 'darwin')

class AlarmSekmesi(ft.Container):
    def __init__(self, page: ft.Page, nav_callback=None):
        super().__init__()
        self.app_page = page
        self.nav_callback = nav_callback
        self.expand = True
        self.padding = ft.Padding.only(left=16, right=16, top=44, bottom=8)
        
        self.alarm_baslik = ft.Text("SİSTEM GÜVENLİ", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_ACCENT_200)
        self.alarm_zaman = ft.Text("", size=13, color=ft.Colors.WHITE54)
        self.alarm_foto_alan = ft.Column(controls=[], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.alarm_ikon = ft.Icon(ft.Icons.SHIELD_OUTLINED, size=64, color=ft.Colors.GREEN_ACCENT_200)
        self._aktif_foto_yolu = None

        self.content = self.arayuzu_olustur()
        db_referans('guvenlik_olayi').listen(self.alarm_cb)

    def arayuzu_olustur(self):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Text("Güvenlik Durumu", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(height=20),
                self.alarm_ikon,
                self.alarm_baslik,
                self.alarm_zaman,
                self.alarm_foto_alan,
                ft.Container(height=10),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER, spacing=10, run_spacing=10,
                    wrap=True,
                    controls=[
                        ft.Button(
                            "Alarm Ekranını Kapat",
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            on_click=self.alarm_sifirla,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN), color=ft.Colors.GREEN_ACCENT_200),
                        ),
                        ft.Button(
                            "Fotoğrafı Kaydet",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=lambda e: foto_kaydet(self._aktif_foto_yolu, self.app_page),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.BLUE), color=ft.Colors.BLUE_ACCENT_200),
                        ),
                    ],
                ),
            ],
        )

    def alarm_sifirla(self, e):
        try:
            db_referans('guvenlik_olayi').set({'durum': 'GUVENLI', 'zaman': '', 'tarih': '', 'foto': '', 'foto_2': '', 'foto_3': '', 'foto_sayisi': 0})
            self.alarm_baslik.value = "SİSTEM GÜVENLİ"
            self.alarm_baslik.color = ft.Colors.GREEN_ACCENT_200
            self.alarm_ikon.name = ft.Icons.SHIELD_OUTLINED
            self.alarm_ikon.color = ft.Colors.GREEN_ACCENT_200
            self.alarm_zaman.value = ""
            self.alarm_foto_alan.controls.clear()
            self.app_page.snack_bar = ft.SnackBar(content=ft.Text("Sistem durumu yeşile döndürüldü."), bgcolor=ft.Colors.GREEN_900)
            self.app_page.snack_bar.open = True
            self.app_page.update()
        except Exception:
            pass

    def alarm_cb(self, event):
        v = event.data
        if not isinstance(v, dict): return
        try:
            if v.get('durum') == 'ALARM':
                self.alarm_baslik.value = "!!! MÜDAHALE TESPİT EDİLDİ !!!"
                self.alarm_baslik.color = ft.Colors.RED_ACCENT_200
                self.alarm_ikon.name = ft.Icons.WARNING_AMBER_ROUNDED
                self.alarm_ikon.color = ft.Colors.RED_ACCENT_200
                self.alarm_zaman.value = f"Zaman: {v.get('tarih', '')} {v.get('zaman', '')}"
                self.alarm_foto_alan.controls.clear()

                fotolar_b64 = [v.get('foto', ''), v.get('foto_2', ''), v.get('foto_3', '')]
                gecerli_fotolar = [(b, i) for i, b in enumerate(fotolar_b64) if b]

                if gecerli_fotolar:
                    aktif_sayfa = [0]
                    temp_yollar = []

                    for b64, i in gecerli_fotolar:
                        yol = os.path.join(tempfile.gettempdir(), f"flet_alarm_{int(time.time()*1000)}_{i}.jpg")
                        try:
                            with open(yol, "wb") as f:
                                f.write(base64.b64decode(b64))
                            temp_yollar.append(yol)
                        except Exception:
                            pass

                    if temp_yollar:
                        self._aktif_foto_yolu = temp_yollar[0]

                    foto_widget = ft.Image(
                        src=temp_yollar[0] if temp_yollar else "",
                        width=320, height=240, fit="contain"
                    )
                    sayfa_etiketi = ft.Text(
                        f"1/{len(temp_yollar)}" if len(temp_yollar) > 1 else "",
                        size=12, color=ft.Colors.WHITE54
                    )

                    def guncelle(idx):
                        foto_widget.src = temp_yollar[idx]
                        self._aktif_foto_yolu = temp_yollar[idx]
                        sayfa_etiketi.value = f"{idx+1}/{len(temp_yollar)}" if len(temp_yollar) > 1 else ""
                        try:
                            if self.page:
                                self.app_page.update()
                        except Exception:
                            pass

                    def onceki(e):
                        if aktif_sayfa[0] > 0:
                            aktif_sayfa[0] -= 1
                            guncelle(aktif_sayfa[0])

                    def sonraki(e):
                        if aktif_sayfa[0] < len(temp_yollar) - 1:
                            aktif_sayfa[0] += 1
                            guncelle(aktif_sayfa[0])

                    self.alarm_foto_alan.controls.append(
                        ft.Container(border_radius=12, clip_behavior=ft.ClipBehavior.ANTI_ALIAS, content=foto_widget)
                    )
                    if len(temp_yollar) > 1:
                        self.alarm_foto_alan.controls.append(
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_color=ft.Colors.WHITE70, on_click=onceki),
                                    sayfa_etiketi,
                                    ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_color=ft.Colors.WHITE70, on_click=sonraki),
                                ]
                            )
                        )
                else:
                    self.alarm_foto_alan.controls.append(
                        ft.Text("Fotoğraf bulunamadı.", color=ft.Colors.WHITE38)
                    )

                if self.nav_callback:
                    self.nav_callback(1)
            else:
                self.alarm_baslik.value = "SİSTEM GÜVENLİ"
                self.alarm_baslik.color = ft.Colors.GREEN_ACCENT_200
                self.alarm_ikon.name = ft.Icons.SHIELD_OUTLINED
                self.alarm_ikon.color = ft.Colors.GREEN_ACCENT_200
                self.alarm_zaman.value = ""
                self.alarm_foto_alan.controls.clear()

            try:
                if self.page:
                    self.app_page.update()
            except Exception:
                pass
        except Exception as e:
            print(f"[HATA] AlarmSekmesi.alarm_cb: {e}")
