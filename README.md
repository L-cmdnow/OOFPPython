# OOFPPython
Repository zum Programm "Student Dashboard" zur Abgabe

## Installationsanleitung (Windows)

### Voraussetzungen

#### Python-Version
Dieses Programm benötigt **Python 3.9 oder höher**.

Die installierte Version lässt sich im Terminal überprüfen:
```
python --version
```

#### Zusätzliche Pakete
Es müssen **keine zusätzlichen Pakete installiert** werden. Das Programm verwendet ausschließlich Module der Python-Standardbibliothek (`sqlite3`, `http.server`, `json` u. a.), die automatisch mit Python mitgeliefert werden.

---

### Programm starten

1. Repository herunterladen oder klonen:
   ```
   git clone https://github.com/L-cmdnow/OOFPPython
   ```

2. In das Projektverzeichnis wechseln:
   ```
   cd OOFPPython
   ```

3. Programm starten:
   ```
   python dashboard.py
   ```
   
   ### Beim ersten Starten wird *student_dashboard.db* erstellt und mit Testdaten gefüllt

4. Das Dashboard im Browser öffnen:
   ```
   http://127.0.0.1:5000
   ```

Das Programm startet einen lokalen Webserver. Solange das Terminal-Fenster geöffnet bleibt, ist das Dashboard erreichbar. Zum Beenden des Servers im Terminal **Ctrl + C** drücken.

