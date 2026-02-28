# OOFPPython
Repository zur Abgabe bei Tutor

## Installationsanleitung (Windows)

### Voraussetzungen

#### Python-Version
Dieses Programm benötigt **Python 3.9 oder höher**.

Die aktuelle Python-Version kann unter [python.org/downloads](https://www.python.org/downloads/) heruntergeladen werden.

> **Wichtig beim Installieren:** Im Installer-Fenster den Haken bei **"Add Python to PATH"** setzen, bevor auf *Install Now* geklickt wird.

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
   git clone <repository-url>
   ```

2. In das Projektverzeichnis wechseln:
   ```
   cd OOFPPython
   ```

3. Programm starten:
   ```
   python dashboard.py
   ```

4. Das Dashboard im Browser öffnen:
   ```
   http://127.0.0.1:5000
   ```

Das Programm startet einen lokalen Webserver. Solange das Terminal-Fenster geöffnet bleibt, ist das Dashboard erreichbar. Zum Beenden des Servers im Terminal **Ctrl + C** drücken.

