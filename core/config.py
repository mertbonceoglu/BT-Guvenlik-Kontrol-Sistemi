# --- Proje Genelinde Paylaşılan Sabit Değerler ---
# Tüm modüller bu dosyadan import eder, böylece değişiklik tek yerden yapılır.

HEDEF_BT_ADRES = "DC:CC:E6:5D:0A:7D"
FIREBASE_PROJE = "pc-bt-guvenlik"
UYGULAMA_VERSIYON = "2.0"

# Mobil bildirimler (ntfy.sh) için kanal adı. Kendinize özel zor bir isim yapabilirsiniz.
NTFY_KANAL_ADI = "pc_bt_guvenlik_mert_8819"

# Bluetooth Güvenlik Ayarları
ONAY_SURESI = 25           # Zayıf sinyal için kilitleme onay süresi (saniye)
SINYAL_KOPMA_SURESI = 35   # Sinyal kesilince kilitleme eşiği (saniye)

# Fotoğraf Ayarları
FOTO_GENISLIK = 640        # Firebase'e gönderilen fotoğraf genişliği (px)
FOTO_YUKSEKLIK = 480       # Firebase'e gönderilen fotoğraf yüksekliği (px)
FOTO_JPEG_KALITE = 65      # JPEG sıkıştırma kalitesi (0-100)
