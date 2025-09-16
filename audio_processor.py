import os
from pydub import AudioSegment
import sys
import librosa
import numpy as np
import whisper

# Globales Whisper-Modell, um es nur einmal zu laden
whisper_model = None

def get_whisper_model():
    """Lädt das Whisper-Modell einmal und gibt es zurück."""
    global whisper_model
    if whisper_model is None:
        # Bestimmt den Pfad für das Modell, abhängig davon, ob die App als .exe läuft
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Die Anwendung wird als PyInstaller-Bundle ausgeführt.
            # Das Modell liegt im temporären Ordner _MEIPASS in einem 'models'-Unterverzeichnis.
            model_root = os.path.join(sys._MEIPASS, "models")
        else:
            # Die Anwendung wird als normales Python-Skript ausgeführt.
            # Das Modell wird im 'models'-Unterverzeichnis des Skript-Verzeichnisses erwartet.
            model_root = os.path.join(os.path.dirname(__file__), "models")

        print(f"Lade Whisper-Modell (base) aus '{model_root}'... Dies kann einen Moment dauern.")
        # 'base' ist ein guter Kompromiss zwischen Geschwindigkeit und Genauigkeit
        whisper_model = whisper.load_model("base", download_root=model_root)
        print("Whisper-Modell geladen.")
    return whisper_model

def convert_to_wav(input_path, output_path):
    """Konvertiert eine Audiodatei in ein hochwertiges WAV-Format (16kHz, 16-bit, mono)."""
    try:
        audio = AudioSegment.from_file(input_path)
        # Whisper erwartet 16kHz Mono-Audio für optimale Ergebnisse
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        print(f"Fehler bei der Konvertierung zu WAV: {e}")
        return False

def assess_audio_quality(wav_path):
    """Bewertet die Qualität einer WAV-Audiodatei."""
    try:
        y, sr = librosa.load(wav_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Signal-Rausch-Verhältnis (einfache Annäherung)
        rms_energy = np.sqrt(np.mean(y**2))
        snr = 20 * np.log10(rms_energy / (np.finfo(float).eps)) if rms_energy > 0 else 0
        
        # Klarheit (Spektraler Schwerpunkt)
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        
        # Probleme und Bewertung
        issues = []
        if sr < 16000:
            issues.append(f"Niedrige Abtastrate ({sr}Hz). Erwartet >= 16kHz.")
        if duration < 5:
            issues.append(f"Kurze Dauer ({duration:.2f}s). Längeres Audio ist besser.")
        if snr < 20:
            issues.append(f"Geringe Signalstärke (SNR: {snr:.2f} dB).")

        # Punktzahl-Berechnung
        score = 100
        score -= len(issues) * 15
        score -= (44100 - min(sr, 44100)) / 44100 * 20 # Bestraft niedrigere Abtastraten
        score -= (30 - min(duration, 30)) / 30 * 10    # Bestraft kürzere Dauer
        score = max(0, score)

        transcription_suitable = score >= 50
        voice_cloning_suitable = score >= 70 and duration >= 30 and sr >= 44100

        return {
            "quality_score": round(score),
            "transcription_suitable": transcription_suitable,
            "voice_cloning_suitable": voice_cloning_suitable,
            "issues": issues,
            "metrics": {
                "duration": round(duration, 2),
                "sample_rate": sr,
                "signal_to_noise_ratio": round(snr, 2),
                "spectral_centroid": round(spectral_centroid, 2)
            }
        }
    except Exception as e:
        return {
            "quality_score": 0,
            "transcription_suitable": False,
            "voice_cloning_suitable": False,
            "issues": [f"Qualitätsbewertung fehlgeschlagen: {e}"],
            "metrics": {}
        }

def transcribe_audio(wav_path):
    """Transkribiert eine Audiodatei mit Whisper."""
    try:
        model = get_whisper_model()
        # fp16=False ist für die CPU-Nutzung erforderlich/stabiler
        result = model.transcribe(wav_path, fp16=False)
        return {
            "text": result["text"],
            "language": result["language"],
            "segments": result["segments"]
        }
    except Exception as e:
        print(f"Transkription fehlgeschlagen: {e}")
        return None

def segment_audio_intelligent(wav_path, transcription_result, segmentation_type):
    """Segmentiert Audio basierend auf der Transkription und dem Segmentierungstyp."""
    if not transcription_result or "segments" not in transcription_result:
        return []

    whisper_segments = transcription_result["segments"]
    final_segments = []

    if segmentation_type == "sentence":
        for seg in whisper_segments:
            final_segments.append({
                "start_time": seg["start"],
                "end_time": seg["end"],
                "text": seg["text"].strip(),
                "type": "sentence"
            })

    elif segmentation_type == "paragraph":
        current_paragraph = ""
        para_start_time = whisper_segments[0]["start"] if whisper_segments else 0

        for i, seg in enumerate(whisper_segments):
            current_paragraph += seg["text"]
            
            is_last_segment = (i == len(whisper_segments) - 1)
            pause_duration = 0
            if not is_last_segment:
                pause_duration = whisper_segments[i+1]["start"] - seg["end"]

            if pause_duration > 2.0 or is_last_segment:
                final_segments.append({
                    "start_time": para_start_time,
                    "end_time": seg["end"],
                    "text": current_paragraph.strip(),
                    "type": "paragraph"
                })
                current_paragraph = ""
                if not is_last_segment:
                    para_start_time = whisper_segments[i+1]["start"]

    elif segmentation_type == "time":
        audio = AudioSegment.from_wav(wav_path)
        duration_ms = len(audio)
        segment_length_ms = 30 * 1000
        for i in range(0, duration_ms, segment_length_ms):
            start_ms = i
            end_ms = min(i + segment_length_ms, duration_ms)
            
            segment_text = "".join([s['text'] for s in whisper_segments if s['start'] < end_ms / 1000 and s['end'] > start_ms / 1000])

            final_segments.append({
                "start_time": start_ms / 1000.0,
                "end_time": end_ms / 1000.0,
                "text": segment_text.strip(),
                "type": "time"
            })

    return final_segments