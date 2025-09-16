# WhatsApp Voice Processor

Eine professionelle Web-Anwendung zur Verarbeitung von WhatsApp Voice-Nachrichten mit intelligenter Segmentierung, Qualitätsbewertung und Transkription.

## Funktionen

### Kernfunktionen
- **Multi-Format-Unterstützung**: Unterstützt alle gängigen Audioformate (MP3, WAV, OPUS, OGG, FLAC, M4A, AAC, WMA)
- **Hochqualitative WAV-Konvertierung**: Automatische Konvertierung zu 44.1kHz, 16-bit WAV für optimale Qualität
- **Intelligente Segmentierung**: 
  - Satzbasierte Segmentierung (empfohlen)
  - Absatzbasierte Segmentierung mit Pausenerkennung
  - Zeitbasierte Segmentierung (30-Sekunden-Blöcke)
- **Qualitätsbewertung**: Automatische Bewertung der Audio-Qualität für Transkription und Voice Cloning
- **Hochpräzise Transkription**: Verwendung von OpenAI Whisper für beste Transkriptionsqualität
- **CSV-Export für TTS Kokei**: Speziell formatierte CSV-Dateien für TTS-Training
- **Batch-Verarbeitung**: Gleichzeitige Verarbeitung mehrerer Dateien
- **Professionelle Benutzeroberfläche**: Moderne React-basierte UI mit Drag & Drop

### Qualitätsbewertung
Die Anwendung bewertet automatisch:
- Sample Rate (höher ist besser für Voice Cloning)
- Signal-Stärke (RMS Energy)
- Rauschpegel (Zero Crossing Rate)
- Spektrale Klarheit (Spectral Centroid)
- Audio-Dauer (länger ist besser für Voice Cloning)

### Segmentierungsoptionen
1. **Satzbasiert**: Segmentierung nach einzelnen Sätzen basierend auf Whisper's natürlicher Spracherkennung
2. **Absatzbasiert**: Gruppierung von Sätzen zu Absätzen basierend auf Sprechpausen (>2 Sekunden)
3. **Zeitbasiert**: Traditionelle 30-Sekunden-Segmente als Fallback

## Installation

### Voraussetzungen
- Python 3.11+
- Node.js 22+
- FFmpeg (für Audio-Konvertierung)

### Setup
1. Repository klonen:
```bash
git clone <repository-url>
cd audio_processor
```

2. Python Virtual Environment erstellen:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

3. Dependencies installieren:
```bash
pip install -r requirements.txt
```

4. Anwendung starten:
```bash
python src/main.py
```

Die Anwendung ist dann unter `http://localhost:5000` verfügbar.

## Verwendung

### 1. Dateien hochladen
- Ziehen Sie Audio-Dateien in den Upload-Bereich oder klicken Sie zum Auswählen
- Unterstützte Formate: MP3, WAV, OPUS, OGG, FLAC, M4A, AAC, WMA
- Mehrere Dateien können gleichzeitig hochgeladen werden

### 2. Segmentierungsart wählen
- **Sätze** (empfohlen): Intelligente Segmentierung nach Sätzen
- **Absätze**: Gruppierung von Sätzen basierend auf Pausen
- **Zeitbasiert**: Feste 30-Sekunden-Segmente

### 3. Verarbeitung starten
- Klicken Sie auf "Dateien verarbeiten"
- Fortschrittsanzeige zeigt Upload-Status
- Ergebnisse werden automatisch angezeigt

### 4. Ergebnisse anzeigen
- **Transkription**: Vollständige Texttranskription mit Spracherkennung
- **Qualität**: Detaillierte Qualitätsbewertung mit Metriken
- **Segmente**: Auflistung aller Segmente mit Zeitstempeln und Text

### 5. CSV-Export
- Klicken Sie auf "CSV für TTS Kokei herunterladen"
- Format: `audio_path|text|speaker_id`
- Kompatibel mit TTS Kokei Training

## API-Endpunkte

### POST /api/audio/upload
Upload und Verarbeitung von Audio-Dateien.

**Parameter:**
- `files`: Audio-Dateien (multipart/form-data)
- `segmentation_type`: 'sentence', 'paragraph', oder 'time'

**Response:**
```json
{
  "results": [
    {
      "file_id": "uuid",
      "original_filename": "audio.mp3",
      "wav_path": "/path/to/converted.wav",
      "quality_assessment": {
        "quality_score": 85,
        "transcription_suitable": true,
        "voice_cloning_suitable": true,
        "issues": [],
        "metrics": {...}
      },
      "transcription": {
        "text": "Transkribierter Text",
        "language": "german",
        "segments": [...]
      },
      "segments": [...],
      "segmentation_type": "sentence",
      "status": "success"
    }
  ]
}
```

### POST /api/audio/export/csv
Export der Verarbeitungsergebnisse als CSV für TTS Kokei.

**Request Body:**
```json
{
  "results": [...]
}
```

**Response:** CSV-Datei zum Download

## Technische Details

### Backend (Flask)
- **Framework**: Flask mit CORS-Unterstützung
- **Audio-Verarbeitung**: pydub, librosa, soundfile
- **Transkription**: OpenAI Whisper (Base-Modell)
- **Qualitätsbewertung**: Librosa-basierte Metriken

### Frontend (React)
- **Framework**: React mit Vite
- **UI-Komponenten**: shadcn/ui mit Tailwind CSS
- **Icons**: Lucide React
- **Features**: Drag & Drop, Fortschrittsanzeigen, Responsive Design

### Unterstützte Audioformate
- **Input**: MP3, WAV, OPUS, OGG, FLAC, M4A, AAC, WMA
- **Output**: WAV (44.1kHz, 16-bit, Mono)

## Qualitätskriterien

### Transkription geeignet (Score ≥ 50)
- Ausreichende Signalstärke
- Akzeptabler Rauschpegel
- Mindestqualität für Spracherkennung

### Voice Cloning geeignet (Score ≥ 70 + ≥30s Dauer)
- Hohe Sample Rate (≥44.1kHz)
- Starkes Signal
- Niedriger Rauschpegel
- Ausreichende Dauer für Training

## Troubleshooting

### Häufige Probleme
1. **Konvertierung fehlgeschlagen**: FFmpeg nicht installiert oder Datei beschädigt
2. **Niedrige Qualitätsbewertung**: Audio-Datei hat schlechte Qualität oder ist zu kurz
3. **Transkription fehlgeschlagen**: Audio nicht verständlich oder zu leise

### Lösungen
- Stellen Sie sicher, dass FFmpeg installiert ist
- Verwenden Sie Audio-Dateien mit guter Qualität
- Überprüfen Sie, dass die Audio-Dateien nicht beschädigt sind

## Lizenz

Dieses Projekt verwendet folgende Open-Source-Bibliotheken:
- OpenAI Whisper (MIT License)
- Flask (BSD License)
- React (MIT License)
- pydub (MIT License)
- librosa (ISC License)

## Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im Repository oder kontaktieren Sie das Entwicklungsteam.

