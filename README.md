# 🛡️ ProxiGuard: Bluetooth & Firebase Tabanlı Bilgisayar Güvenlik Sistemi

ProxiGuard, bilgisayarınızı masada bırakıp uzaklaştığınızda Bluetooth sinyal gücünü (RSSI) takip ederek bilgisayarınızı **otomatik olarak kilitleyen** ve kilitliyken bilgisayara yetkisiz müdahale (fare hareketi, şarj kablosunun çekilmesi vb.) yapıldığında **webcam ile fotoğraf çekip Firebase ve ntfy üzerinden telefonunuza anlık bildirim gönderen** akıllı bir güvenlik ve kontrol sistemidir.

---

## ✨ Özellikler

- 📶 **Bluetooth RSSI Takibi:** Belirlediğiniz telefon veya Bluetooth cihazı bilgisayardan uzaklaştığında (sinyal zayıfladığında veya koptuğunda) Windows otomatik kilitlenir (`Win + L`).
- 📸 **Sessiz Pusu & Fotoğraflı Müdahale Yakalama:** Bilgisayar kilitliyken fare oynatılırsa veya şarj kablosu çıkarılırsa webcam arka planda sessizce 3 kare fotoğraf çeker.
- ☁️ **Firebase Entegrasyonu:** Çekilen fotoğraflar ve olay geçmişi Firebase Realtime Database'e anında yüklenir.
- 🔔 **Anlık Mobil Bildirimler:** ntfy.sh entegrasyonu sayesinde telefonunuza anında uyarı bildirimi düşer.
- 🖥️ **Modern Masaüstü Paneli:** Flet tabanlı şık koyu tema arayüz ile canlı durum takibi, olay geçmişi, alarm kontrolü ve Bluetooth cihaz tarama/eşleştirme.
- 🪟 **Sistem Tepsisi (Tray) Desteği:** Servis arka planda sessizce çalışır, sistem tepsisinden yönetilebilir.
- 📱 **Mobil / APK Desteği:** Flet ile Android APK olarak da derlenebilir.

---

## 📁 Proje Dizin Yapısı

```text
bt_guvenlik/
├── assets/                  # Uygulama ikonları
├── core/
│   ├── config.py            # Paylaşılan sabitler (gecikmeler, eşikler, ntfy kanalı)
│   ├── firebase_baglanti.py # Firebase Realtime Database bağlantı modülü
│   └── firebase_key.example.json # Firebase servis hesabı anahtarı şablonu
├── servis/
│   ├── kamera_motoru.py     # Webcam fotoğraf çekme ve pusu motoru
│   ├── sistem_izleyici.py   # Pil, şarj ve sistem durumu izleyici
│   ├── sistem_tepsisi.py    # Windows sistem tepsisi (pystray) entegrasyonu
│   └── kapatma_popup.py     # Servis kapatma onay penceresi
├── ui/
│   ├── dashboard.py         # Canlı durum ve sinyal gösterge paneli
│   ├── alarm.py             # Alarm durum ekranı
│   ├── gecmis.py            # Olay ve fotoğraf geçmişi ekranı
│   ├── ayarlar.py           # Bluetooth eşleştirme ve ayarlar
│   └── bilesenler.py        # Özel UI bileşenleri
├── araclar/
│   ├── Kur.bat              # Otomatik ortam ve paket kurulum betiği
│   ├── Servisi_Baslat.bat   # Arka plan servisini başlatan betik
│   ├── Baslangica_Ekle.bat  # Windows başlangıcına ekleme betiği
│   └── APK_Derle.bat        # Mobil APK derleme betiği
├── main.py                  # Masaüstü Kontrol Paneli arayüzü
├── bt_servis.py             # Bluetooth arka plan güvenlik servisi
├── requirements-pc.txt      # Gerekli Python bağımlılıkları
└── pyproject.toml           # Proje konfigürasyonu
```

---

## 🚀 Kurulum ve Başlangıç

### 1. Gereksinimler
- **Windows 10 / 11**
- **Python 3.10 - 3.13** (Kurulum sırasında *"Add Python to PATH"* seçilmelidir)
- Bilgisayarda Bluetooth adaptörü ve Webcam

### 2. Depoyu İndirin
```bash
git clone https://github.com/mertbonceoglu/BT-Guvenlik-Kontrol-Sistemi.git
cd BT-Guvenlik-Kontrol-Sistemi
```

### 3. Otomatik Kurulum
`araclar` klasöründeki `Kur.bat` dosyasını çalıştırın veya terminalden şu komutları verin:
```bash
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements-pc.txt
```

### 4. Firebase Yapılandırması
1. [Firebase Console](https://console.firebase.google.com/) üzerinden bir proje oluşturun ve **Realtime Database** etkinleştirin.
2. Proje Ayarları > *Hizmet Hesapları (Service Accounts)* bölümünden yeni bir **Özel Anahtar Oluşturun (Generate new private key)**.
3. İndirdiğiniz JSON dosyasının adını `firebase_key.json` olarak değiştirip `core/` klasörü altına kopyalayın.
4. `core/firebase_baglanti.py` içindeki `FIREBASE_URL` adresini kendi Firebase veritabanı adresinizle güncelleyin.

### 5. Bildirim Ayarı (ntfy)
- Telefonunuza **ntfy** uygulamasını (Google Play / App Store) indirin.
- `core/config.py` dosyasındaki `NTFY_KANAL_ADI` değerini kendinize özel belirleyin ve aynı isimdeki kanala telefonunuzdaki ntfy uygulamasından abone olun.

---

## 🎮 Kullanım

### Telefonu Eşleştirme ve Kontrol Paneli
Masaüstü panelini açmak için:
```bash
.\venv\Scripts\python.exe main.py
```
- **Ayarlar** sekmesine gidin.
- **Cihaz Tara** butonuna basarak Bluetooth cihazlarınızı listeleyin ve telefonunuzu seçerek eşleştirin.

### Güvenlik Servisini Başlatma
- Ana klasördeki `Servisi_Baslat.bat` dosyasına çift tıklayın.
- Servis arka planda çalışmaya başlar ve sağ alttaki sistem tepsisine (Tray) yerleşir.
- Telefonunuzu yanınıza alıp bilgisayardan uzaklaştığınızda bilgisayarınız kilitlenecektir.

---

## 🔒 Güvenlik & Gizlilik Notu
> `core/firebase_key.json`, çekilen fotoğraflar (`logs/foto/`) ve log dosyaları hassas veri içerdiğinden `.gitignore` ile korunmaktadır ve asla GitHub'a yüklenmemelidir.
