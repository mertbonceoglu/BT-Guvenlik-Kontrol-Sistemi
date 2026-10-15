import firebase_admin
from firebase_admin import credentials, db
import os
import threading

_LOCK = threading.Lock()

ANA_DIZIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Flet APK ortamı için
ASSETS_DIR = os.environ.get("FLET_ASSETS_DIR", ANA_DIZIN)
KEY_YOLU = os.path.join(ASSETS_DIR, "firebase_key.json")
if not os.path.exists(KEY_YOLU):
    KEY_YOLU = os.path.join(ANA_DIZIN, "core", "firebase_key.json")

FIREBASE_URL = "https://pc-bt-guvenlik-default-rtdb.europe-west1.firebasedatabase.app/"

def firebase_baslat():
    """Firebase bağlantısını kurar."""
    with _LOCK:
        if not firebase_admin._apps:
            cred = credentials.Certificate(KEY_YOLU)
            firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})

def db_referans(dugum_adi):
    """Verilen düğüm adıyla Firebase Realtime Database referansı döner."""
    if not firebase_admin._apps:
        firebase_baslat()
    return db.reference(dugum_adi)
