On Error Resume Next

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' bt_servis.py dosyasinin bulundugu dizine git
strPath = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
rootPath = fso.GetAbsolutePathName(strPath & "..") & "\"

If Not fso.FolderExists(rootPath & "logs") Then
    fso.CreateFolder(rootPath & "logs")
End If

' Log dosyasi
logFile = rootPath & "logs\servis_baslangic_log.txt"

Sub LogYaz(mesaj)
    Set f = fso.OpenTextFile(logFile, 8, True)
    f.WriteLine Now & " | " & mesaj
    f.Close
End Sub

' --- Zaten calisiyor mu kontrol et (cift calismayi engelle) ---
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set procs = wmi.ExecQuery("SELECT CommandLine FROM Win32_Process WHERE Name='pythonw.exe'")
For Each p In procs
    If InStr(LCase(p.CommandLine), "bt_servis.py") > 0 Then
        LogYaz "Servis zaten calisiyor, tekrar baslatilmadi."
        WScript.Quit
    End If
Next

' --- Windows acilisinda ag baglantisi icin bekle (15 saniye) ---
' Sadece baslangicta (startup klasorunden) calistirildiginda bekler
args = WScript.Arguments.Count
bekleSure = 0
If InStr(LCase(WScript.ScriptFullName), "startup") > 0 Then
    bekleSure = 30
End If

' Komut satirindan da bekleme suresi verilebilir
If args > 0 Then
    bekleSure = CInt(WScript.Arguments(0))
End If

If bekleSure > 0 Then
    LogYaz "Ag baglantisi bekleniyor (" & bekleSure & " saniye)..."
    WScript.Sleep bekleSure * 1000
    LogYaz "Bekleme tamamlandi, servis baslatiliyor."
End If

' --- Servisi baslat ---
LogYaz "Servis baslatma denemesi..."

If fso.FileExists(rootPath & "venv\Scripts\pythonw.exe") Then
    WshShell.CurrentDirectory = rootPath
    WshShell.Run """" & rootPath & "venv\Scripts\pythonw.exe"" """ & rootPath & "bt_servis.py""", 0, False
    LogYaz "pythonw.exe (venv) ile baslatildi."
Else
    WshShell.CurrentDirectory = rootPath
    WshShell.Run "pythonw.exe """ & rootPath & "bt_servis.py""", 0, False
    LogYaz "pythonw.exe (global) ile baslatildi."
End If

If Err.Number <> 0 Then
    LogYaz "HATA: " & Err.Description & " (Kod: " & Err.Number & ")"
Else
    LogYaz "Islem basariyla tamamlandi."
End If
