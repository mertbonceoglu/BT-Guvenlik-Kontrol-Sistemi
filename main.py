import flet as ft
import os
from core.firebase_baglanti import firebase_baslat, KEY_YOLU
from ui.dashboard import DashboardSekmesi
from ui.alarm import AlarmSekmesi
from ui.gecmis import GecmisSekmesi
from ui.ayarlar import AyarlarSekmesi

def main(page: ft.Page):
    page.title = "ProxiGuard Paneli"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0D1117"
    page.padding = 0

    try:
        firebase_baslat()
    except Exception as e:
        page.add(ft.Text(f"Firebase Hatası: {e}\nKEY: {KEY_YOLU}", color=ft.Colors.RED, size=12))
        return

    ayarlar_sayfasi = AyarlarSekmesi(page)
    
    def gecmis_guncellendi_cb(toplam_sayi):
        ayarlar_sayfasi.set_toplam_alarm(toplam_sayi)

    dashboard_sayfasi = DashboardSekmesi(page)
    gecmis_sayfasi = GecmisSekmesi(page, on_gecmis_guncellendi=gecmis_guncellendi_cb)

    # alarm_sayfasi, sayfa_degistir'den ÖNCE tanımlanmalı (Firebase callback race condition)
    alarm_sayfasi = AlarmSekmesi(page, nav_callback=lambda idx: sayfa_degistir(idx))
    
    icerik_alani = ft.Container(expand=True, content=dashboard_sayfasi)

    nav_bar = ft.NavigationBar(
        bgcolor=ft.Colors.with_opacity(0.95, "#161B22"),
        indicator_color=ft.Colors.with_opacity(0.15, ft.Colors.CYAN),
        selected_index=0,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD, label="Panel"),
            ft.NavigationBarDestination(icon=ft.Icons.SHIELD_OUTLINED, selected_icon=ft.Icons.SHIELD, label="Alarm"),
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, selected_icon=ft.Icons.HISTORY, label="Geçmiş"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Ayarlar"),
        ],
    )

    sayfalar = [dashboard_sayfasi, alarm_sayfasi, gecmis_sayfasi, ayarlar_sayfasi]

    def sayfa_degistir(idx):
        nav_bar.selected_index = idx
        icerik_alani.content = sayfalar[idx]
        page.update()

    nav_bar.on_change = lambda e: sayfa_degistir(e.control.selected_index)
    page.navigation_bar = nav_bar
    page.add(icerik_alani)

if __name__ == "__main__":
    ft.run(main)
    os._exit(0)  # Firebase listener thread'leri süreç kapanmasını engellemesin