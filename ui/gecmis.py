import flet as ft
import base64
import os
import sys
import tempfile
import time
from core.firebase_baglanti import db_referans
from ui.bilesenler import foto_kaydet

PC_ORTAMI = sys.platform in ('win32', 'linux', 'darwin')

class GecmisSekmesi(ft.Container):
    def __init__(self, page: ft.Page, on_gecmis_guncellendi=None):
        super().__init__()
        self.app_page = page
        self.on_gecmis_guncellendi = on_gecmis_guncellendi
        self.expand = True
        self.padding = ft.Padding.only(left=0, right=0, top=44, bottom=8)
        
        self.gecmis_liste = ft.ListView(spacing=8, expand=True, padding=ft.Padding.symmetric(horizontal=16))
        self.content = self.arayuzu_olustur()
        db_referans('alarm_gecmisi').listen(self.gecmis_cb)

    def arayuzu_olustur(self):
        return ft.Column(
            spacing=12, expand=True,
            controls=[
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=16),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Olay Geçmişi", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_ACCENT_200,
                                tooltip="Geçmişi Temizle",
                                on_click=self.gecmisi_temizle,
                            ),
                        ],
                    ),
                ),
                self.gecmis_liste,
            ],
        )

    def gecmisi_temizle(self, e):
        try:
            db_referans('alarm_gecmisi').delete()
            self.gecmis_liste.controls.clear()
            self.gecmis_liste.controls.append(ft.Text("Geçmiş temizlendi.", size=13, color=ft.Colors.WHITE38))
            self.app_page.update()
        except Exception:
            pass

    def _b64_to_tempfile(self, b64_str, suffix=""):
        """Base64 string'i geçici dosyaya yazar, dosya yolunu döndürür."""
        if not b64_str:
            return None
        try:
            yol = os.path.join(tempfile.gettempdir(), f"flet_foto_{int(time.time()*1000)}{suffix}.jpg")
            with open(yol, "wb") as f:
                f.write(base64.b64decode(b64_str))
            return yol
        except Exception:
            return None

    def _foto_popup_ac(self, fotolar_b64, zaman_str):
        """fotolar_b64: [foto1_b64, foto2_b64, foto3_b64] listesi"""
        try:
            aktif_sayfa = [0]

            temp_dosyalar = []
            gecerli_fotolar = []
            for i, b64 in enumerate(fotolar_b64):
                yol = self._b64_to_tempfile(b64, suffix=f"_f{i+1}")
                if yol:
                    gecerli_fotolar.append(yol)
                    temp_dosyalar.append(yol)

            foto_gosterici = ft.Image(src="", width=350, height=260, fit="contain")
            sayfa_gostergesi = ft.Text("", size=12, color=ft.Colors.WHITE54)

            def guncelle_foto(idx):
                if gecerli_fotolar:
                    foto_gosterici.src = gecerli_fotolar[idx]
                    sayfa_gostergesi.value = f"Fotoğraf {idx+1}/{len(gecerli_fotolar)}"
                    if self.page:
                        self.app_page.update()

            def onceki(e):
                if aktif_sayfa[0] > 0:
                    aktif_sayfa[0] -= 1
                    guncelle_foto(aktif_sayfa[0])

            def sonraki(e):
                if aktif_sayfa[0] < len(gecerli_fotolar) - 1:
                    aktif_sayfa[0] += 1
                    guncelle_foto(aktif_sayfa[0])

            def close_dlg(e):
                dlg.open = False
                self.app_page.update()

            if gecerli_fotolar:
                guncelle_foto(0)

            navigasyon = ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_LEFT,
                        icon_color=ft.Colors.WHITE70,
                        on_click=onceki,
                        visible=len(gecerli_fotolar) > 1,
                    ),
                    sayfa_gostergesi,
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT,
                        icon_color=ft.Colors.WHITE70,
                        on_click=sonraki,
                        visible=len(gecerli_fotolar) > 1,
                    ),
                ]
            )

            icerik = ft.Column(
                controls=[
                    ft.Container(
                        border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=foto_gosterici if gecerli_fotolar else ft.Text("Fotoğraf bulunamadı.", color=ft.Colors.WHITE38),
                    ),
                    navigasyon,
                    ft.Text(zaman_str, size=12, color=ft.Colors.WHITE38),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            )

            def kaydet(e):
                if gecerli_fotolar:
                    foto_kaydet(gecerli_fotolar[aktif_sayfa[0]], self.app_page)

            dlg = ft.AlertDialog(
                title=ft.Text("Müdahale Fotoğrafları"),
                content=icerik,
                actions=[
                    ft.ElevatedButton(
                        "Kaydet",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=kaydet,
                        visible=bool(gecerli_fotolar),
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE)
                    ),
                    ft.ElevatedButton(
                        "Kapat", on_click=close_dlg,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            # Hem eski hem yeni Flet API uyumlu
            try:
                self.app_page.open(dlg)
            except (AttributeError, TypeError):
                self.app_page.overlay.append(dlg)
                dlg.open = True
                self.app_page.update()

        except Exception as err:
            print(f"\n[POPUP HATA]: {err}\n")

    def gecmis_cb(self, event):
        try:
            v = db_referans('alarm_gecmisi').get()
            if v is None:
                self.gecmis_liste.controls.clear()
                self.gecmis_liste.controls.append(ft.Text("Henüz olay kaydı yok.", size=13, color=ft.Colors.WHITE38))
                if self.on_gecmis_guncellendi:
                    self.on_gecmis_guncellendi(0)
                if self.page:
                    self.app_page.update()
                return

            if not isinstance(v, dict): return

            self.gecmis_liste.controls.clear()
            items = sorted(v.items(), key=lambda x: x[0], reverse=True)

            if self.on_gecmis_guncellendi:
                self.on_gecmis_guncellendi(len(items))

            for key, olay in items:
                if not isinstance(olay, dict): continue

                # Tüm fotoğrafları topla
                fotolar_b64 = [
                    olay.get('foto', ''),
                    olay.get('foto_2', ''),
                    olay.get('foto_3', ''),
                ]
                foto_sayisi = olay.get('foto_sayisi', 1)
                zaman_str = f"{olay.get('tarih', '')} {olay.get('zaman', '')}"

                def foto_goster(e, f=fotolar_b64, z=zaman_str):
                    self._foto_popup_ac(f, z)

                foto_var = any(fotolar_b64)
                self.gecmis_liste.controls.append(
                    ft.Container(
                        border_radius=12, padding=ft.Padding.all(12),
                        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.RED)),
                        on_click=foto_goster if foto_var else None,
                        ink=foto_var,
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_ACCENT_200, size=28),
                                ft.Column(
                                    spacing=2, expand=True,
                                    controls=[
                                        ft.Text("Müdahale Tespit Edildi", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_ACCENT_200),
                                        ft.Text(zaman_str, size=12, color=ft.Colors.WHITE54),
                                    ],
                                ),
                                ft.Row(spacing=4, controls=[
                                    ft.Icon(ft.Icons.PHOTO_LIBRARY_OUTLINED if foto_sayisi > 1 else ft.Icons.PHOTO_OUTLINED,
                                            color=ft.Colors.WHITE38, size=18),
                                    ft.Text(str(foto_sayisi), size=11, color=ft.Colors.WHITE38) if foto_sayisi > 1 else ft.Text(""),
                                ]),
                            ],
                        ),
                    )
                )

            if not self.gecmis_liste.controls:
                self.gecmis_liste.controls.append(ft.Text("Henüz olay kaydı yok.", size=13, color=ft.Colors.WHITE38))

            if self.page:
                self.app_page.update()
        except Exception:
            pass
