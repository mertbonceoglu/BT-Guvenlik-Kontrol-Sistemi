"""
Bilgisayar ekranında geri sayımlı kapatma uyarısı (tkinter).
Argüman olarak saniye alır (örn: python kapatma_popup.py 15)
Çıkış kodları:
0: Süre doldu (kapatma onaylandı)
1: Kullanıcı iptal etti
"""
import sys
import tkinter as tk

def main():
    try:
        sure = int(sys.argv[1])
    except (IndexError, ValueError):
        sure = 15

    root = tk.Tk()
    root.title("Kapatma Uyarısı")
    root.configure(bg="#1a1a2e")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    w, h = 400, 200
    root.geometry(f"{w}x{h}+{(root.winfo_screenwidth()-w)//2}+{(root.winfo_screenheight()-h)//3}")

    tk.Label(root, text="⚠ BİLGİSAYAR KAPANACAK", font=("Segoe UI", 15, "bold"), fg="#ff4757", bg="#1a1a2e").pack(pady=(16, 4))
    sayac_lbl = tk.Label(root, text=str(sure), font=("Segoe UI", 40, "bold"), fg="#ff6b6b", bg="#1a1a2e")
    sayac_lbl.pack(pady=(4, 2))
    tk.Label(root, text="saniye sonra bilgisayar kapanacak", font=("Segoe UI", 10), fg="#666680", bg="#1a1a2e").pack()

    kalan = [sure]

    def iptal_et():
        # Kullanıcı iptal etti: Çıkış kodu 1
        root.destroy()
        sys.exit(1)

    tk.Button(root, text="❌ İPTAL ET", font=("Segoe UI", 11, "bold"), fg="white", bg="#e74c3c",
              activebackground="#c0392b", relief="flat", cursor="hand2", padx=16, pady=4,
              command=iptal_et).pack(pady=(10, 0))

    root.protocol("WM_DELETE_WINDOW", iptal_et)

    def geri_say():
        kalan[0] -= 1
        if kalan[0] <= 0:
            # Süre doldu: Çıkış kodu 0
            root.destroy()
            sys.exit(0)
            
        sayac_lbl.configure(text=str(kalan[0]))
        if kalan[0] <= 5:
            sayac_lbl.configure(fg="#ff0000" if kalan[0] % 2 == 0 else "#ff4757")
        root.after(1000, geri_say)

    root.after(1000, geri_say)
    root.mainloop()

if __name__ == "__main__":
    main()
