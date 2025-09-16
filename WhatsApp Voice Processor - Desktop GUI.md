# WhatsApp Voice Processor - Desktop GUI

Eine benutzerfreundliche Desktop-Anwendung zur Verarbeitung von WhatsApp-Sprachnachrichten mit automatischer Transkription, Qualitätsbewertung und intelligenter Segmentierung.

## Features

- **Datei-Upload**: Unterstützt verschiedene Audioformate (MP3, WAV, OPUS, OGG, FLAC, M4A, AAC, WMA)
- **Automatische Transkription**: Verwendet OpenAI Whisper für hochpräzise Spracherkennung
- **Qualitätsbewertung**: Bewertet die Audio-Qualität für Transkription und Voice Cloning
- **Intelligente Segmentierung**: 
  - Satzbasierte Segmentierung (empfohlen)
  - Absatzbasierte Segmentierung
  - Zeitbasierte Segmentierung (30s Intervalle)
- **Fortschrittsanzeige**: Echtzeit-Updates während der Verarbeitung
- **Benutzerfreundliche Oberfläche**: Intuitive Tkinter-GUI

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- Alle Abhängigkeiten aus `requirements.txt`

### Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### Anwendung starten

```bash
python gui_app.py
```

## Verwendung

1. **Dateien auswählen**: Klicken Sie auf "Dateien auswählen" und wählen Sie Ihre Audiodateien aus
2. **Segmentierungsart wählen**: Wählen Sie die gewünschte Segmentierungsmethode:
   - **Sätze**: Segmentiert basierend auf natürlichen Satzpausen (empfohlen)
   - **Absätze**: Gruppiert Sätze zu längeren Absätzen
   - **Zeitbasiert**: Teilt Audio in 30-Sekunden-Segmente
3. **Verarbeitung starten**: Klicken Sie auf "Dateien verarbeiten"
4. **Ergebnisse anzeigen**: Die Verarbeitungsergebnisse werden im unteren Bereich angezeigt

## Windows Executable erstellen

### Automatischer Build (empfohlen)

Verwenden Sie das mitgelieferte Build-Script:

```bash
python build_exe.py
```

Das Script:
- Installiert PyInstaller automatisch
- Erstellt eine optimierte .spec-Datei
- Baut die ausführbare Datei
- Die fertige .exe-Datei befindet sich im `dist/` Ordner

### Manueller Build

1. PyInstaller installieren:
```bash
pip install pyinstaller
```

2. Executable erstellen:
```bash
pyinstaller whatsapp_voice_processor_windows.spec
```

### Build-Anforderungen für Windows

- Windows 10/11
- Python 3.8+
- Alle Projektabhängigkeiten installiert
- Mindestens 4GB freier Speicherplatz für den Build-Prozess

## Projektstruktur

```
├── gui_app.py                          # Haupt-GUI-Anwendung
├── audio_processor.py                  # Audio-Verarbeitungslogik
├── requirements.txt                    # Python-Abhängigkeiten
├── build_exe.py                       # Automatisches Build-Script
├── whatsapp_voice_processor.spec      # PyInstaller-Konfiguration (Linux)
├── whatsapp_voice_processor_windows.spec # PyInstaller-Konfiguration (Windows)
└── README_GUI.md                      # Diese Dokumentation
```

## Technische Details

### Audio-Verarbeitung

- **Konvertierung**: Alle Eingabeformate werden zu hochqualitativem WAV konvertiert
- **Qualitätsbewertung**: Analysiert RMS-Energie, Zero-Crossing-Rate und spektrale Eigenschaften
- **Transkription**: Verwendet Whisper "base" Modell für optimale Balance zwischen Geschwindigkeit und Genauigkeit
- **Segmentierung**: Intelligente Algorithmen basierend auf Sprachpausen und semantischen Grenzen

### GUI-Features

- **Threading**: Verhindert das Einfrieren der GUI während der Verarbeitung
- **Fortschrittsbalken**: Zeigt den aktuellen Verarbeitungsfortschritt
- **Echtzeit-Updates**: Live-Status-Updates im Ergebnisbereich
- **Fehlerbehandlung**: Robuste Fehlerbehandlung mit benutzerfreundlichen Meldungen

### Performance-Optimierungen

- **Einmaliges Modell-Laden**: Whisper-Modell wird nur einmal geladen
- **Temporäre Dateien**: Automatische Bereinigung von temporären Dateien
- **Speicher-Management**: Effiziente Speichernutzung durch schrittweise Verarbeitung

## Fehlerbehebung

### Häufige Probleme

1. **"Whisper-Modell kann nicht geladen werden"**
   - Stellen Sie sicher, dass eine Internetverbindung besteht (für ersten Download)
   - Überprüfen Sie, ob genügend Speicherplatz vorhanden ist

2. **"Audio-Konvertierung fehlgeschlagen"**
   - Überprüfen Sie, ob die Audiodatei nicht beschädigt ist
   - Stellen Sie sicher, dass das Dateiformat unterstützt wird

3. **"Anwendung reagiert nicht"**
   - Die Verarbeitung läuft im Hintergrund - warten Sie auf Abschluss
   - Bei sehr großen Dateien kann die Verarbeitung mehrere Minuten dauern

### Build-Probleme

1. **"PyInstaller nicht gefunden"**
   ```bash
   pip install pyinstaller
   ```

2. **"Abhängigkeiten fehlen"**
   ```bash
   pip install -r requirements.txt
   ```

3. **"Executable startet nicht"**
   - Überprüfen Sie, ob alle Abhängigkeiten korrekt gepackt wurden
   - Verwenden Sie das bereitgestellte .spec-File für optimale Kompatibilität

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe LICENSE-Datei für Details.

## Support

Bei Problemen oder Fragen erstellen Sie bitte ein Issue im Projekt-Repository oder kontaktieren Sie das Entwicklungsteam.

