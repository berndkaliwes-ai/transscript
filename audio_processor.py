import os
import tempfile
import uuid
from pydub import AudioSegment
import librosa
import soundfile as sf
import numpy as np
import json
import whisper
import speech_recognition as sr
import csv
import io

# Load Whisper model (using base model for balance of speed and accuracy)
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model...")
        whisper_model = whisper.load_model("base")
        print("Whisper model loaded.")
    return whisper_model

# Allowed file extensions
ALLOWED_EXTENSIONS = {"mp3", "wav", "opus", "ogg", "flac", "m4a", "aac", "wma"}

def allowed_file(filename):
    if not filename or "." not in filename:
        return False
    name_parts = filename.rsplit(".", 1)
    if not name_parts[0]: # Check if there's a name before the dot
        return False
    return name_parts[1].lower() in ALLOWED_EXTENSIONS

def convert_to_wav(input_path, output_path):
    """Convert audio file to high-quality WAV format"""
    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(44100).set_channels(1).set_sample_width(2)
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        print(f"Error converting to WAV: {e}")
        return False

def segment_audio_intelligent(audio_path, transcription_result, segmentation_type='sentence'):
    """Segment audio based on transcription segments (sentences/paragraphs)"""
    try:
        audio = AudioSegment.from_wav(audio_path)
        segments = []
        
        if segmentation_type == 'sentence':
            for i, segment in enumerate(transcription_result.get('segments', [])):
                start_ms = int(segment['start'] * 1000)
                end_ms = int(segment['end'] * 1000)
                
                audio_segment = audio[start_ms:end_ms]
                segments.append({
                    'audio': audio_segment,
                    'start_time': segment['start'],
                    'end_time': segment['end'],
                    'text': segment['text'].strip(),
                    'type': 'sentence'
                })
        
        elif segmentation_type == 'paragraph':
            current_paragraph = []
            current_start = None
            
            for i, segment in enumerate(transcription_result.get('segments', [])):
                if current_start is None:
                    current_start = segment['start']
                
                current_paragraph.append(segment)
                
                is_end_of_paragraph = False
                if i < len(transcription_result['segments']) - 1:
                    next_segment = transcription_result['segments'][i + 1]
                    pause_duration = next_segment['start'] - segment['end']
                    if pause_duration > 2.0:
                        is_end_of_paragraph = True
                else:
                    is_end_of_paragraph = True
                
                if is_end_of_paragraph and current_paragraph:
                    start_ms = int(current_start * 1000)
                    end_ms = int(segment['end'] * 1000)
                    
                    audio_segment = audio[start_ms:end_ms]
                    
                    paragraph_text = ' '.join([s['text'].strip() for s in current_paragraph])
                    
                    segments.append({
                        'audio': audio_segment,
                        'start_time': current_start,
                        'end_time': segment['end'],
                        'text': paragraph_text,
                        'type': 'paragraph'
                    })
                    
                    current_paragraph = []
                    current_start = None
        
        elif segmentation_type == 'time':
            segment_length_ms = 30000
            for i in range(0, len(audio), segment_length_ms):
                segment = audio[i:i + segment_length_ms]
                segments.append({
                    'audio': segment,
                    'start_time': i / 1000.0,
                    'end_time': min((i + segment_length_ms) / 1000.0, len(audio) / 1000.0),
                    'text': '',
                    'type': 'time',
                    'duration': (segment_length_ms / 1000.0)
                })
        
        return segments
    except Exception as e:
        print(f"Error in intelligent segmentation: {e}")
        return []

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper"""
    try:
        model = get_whisper_model()
        result = model.transcribe(audio_path)
        
        return {
            'text': result['text'].strip(),
            'language': result['language'],
            'segments': [
                {
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': seg['text'].strip()
                }
                for seg in result['segments']
            ]
        }
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return {
            'text': '',
            'language': 'unknown',
            'segments': [],
            'error': str(e)
        }

def assess_audio_quality(audio_path):
    """Assess audio quality for transcription and voice cloning"""
    try:
        y, sr = librosa.load(audio_path, sr=None)
        
        rms = librosa.feature.rms(y=y)[0]
        rms_mean = np.mean(rms)
        
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = np.mean(zcr)
        
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_centroid_mean = np.mean(spectral_centroid)
        
        duration = len(y) / sr
        
        sample_rate = sr
        
        quality_score = 0
        issues = []
        
        if sample_rate >= 44100:
            quality_score += 25
        elif sample_rate >= 22050:
            quality_score += 15
            issues.append("Sample rate could be higher for optimal voice cloning")
        else:
            quality_score += 5
            issues.append("Low sample rate - not recommended for voice cloning")
        
        if rms_mean > 0.01:
            quality_score += 25
        elif rms_mean > 0.005:
            quality_score += 15
            issues.append("Signal level is low")
        else:
            quality_score += 5
            issues.append("Very low signal level - may affect transcription quality")
        
        if zcr_mean < 0.1:
            quality_score += 25
        elif zcr_mean < 0.2:
            quality_score += 15
            issues.append("Moderate noise detected")
        else:
            quality_score += 5
            issues.append("High noise level detected")
        
        if duration >= 60:
            quality_score += 25
        elif duration >= 30:
            quality_score += 20
        elif duration >= 10:
            quality_score += 15
        else:
            quality_score += 5
            issues.append("Short duration - may not be suitable for voice cloning")
        
        transcription_suitable = quality_score >= 50
        voice_cloning_suitable = quality_score >= 70 and duration >= 30
        
        return {
            'quality_score': quality_score,
            'transcription_suitable': transcription_suitable,
            'voice_cloning_suitable': voice_cloning_suitable,
            'issues': issues,
            'metrics': {
                'duration': duration,
                'sample_rate': sample_rate,
                'rms_energy': float(rms_mean),
                'zero_crossing_rate': float(zcr_mean),
                'spectral_centroid': float(spectral_centroid_mean)
            }
        }
    except Exception as e:
        print(f"Error assessing audio quality: {e}")
        return {
            'quality_score': 0,
            'transcription_suitable': False,
            'voice_cloning_suitable': False,
            'issues': [f"Error analyzing audio: {str(e)}"],
            'metrics': {}
        }

