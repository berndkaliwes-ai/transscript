from flask import Blueprint, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from pydub import AudioSegment
import librosa
import soundfile as sf
import numpy as np
from datetime import datetime
import json
import whisper
import speech_recognition as sr
import csv
import io

audio_bp = Blueprint('audio', __name__)

# Load Whisper model (using base model for balance of speed and accuracy)
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("base")
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
        # Load audio with pydub
        audio = AudioSegment.from_file(input_path)
        
        # Convert to high quality WAV (44.1kHz, 16-bit)
        audio = audio.set_frame_rate(44100).set_channels(1).set_sample_width(2)
        
        # Export as WAV
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        print(f"Error converting to WAV: {e}")
        return False
