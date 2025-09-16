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

def segment_audio_intelligent(audio_path, transcription_result, segmentation_type='sentence'):
    """Segment audio based on transcription segments (sentences/paragraphs)"""
    try:
        audio = AudioSegment.from_wav(audio_path)
        segments = []
        
        if segmentation_type == 'sentence':
            # Use Whisper's built-in sentence segmentation
            for i, segment in enumerate(transcription_result.get('segments', [])):
                start_ms = int(segment['start'] * 1000)
                end_ms = int(segment['end'] * 1000)
                
                # Extract audio segment
                audio_segment = audio[start_ms:end_ms]
                segments.append({
                    'audio': audio_segment,
                    'start_time': segment['start'],
                    'end_time': segment['end'],
                    'text': segment['text'].strip(),
                    'type': 'sentence'
                })
        
        elif segmentation_type == 'paragraph':
            # Group sentences into paragraphs based on pauses
            current_paragraph = []
            current_start = None
            
            for i, segment in enumerate(transcription_result.get('segments', [])):
                if current_start is None:
                    current_start = segment['start']
                
                current_paragraph.append(segment)
                
                # Check if this is the end of a paragraph (long pause or end of transcription)
                is_end_of_paragraph = False
                if i < len(transcription_result['segments']) - 1:
                    next_segment = transcription_result['segments'][i + 1]
                    pause_duration = next_segment['start'] - segment['end']
                    if pause_duration > 2.0:  # 2 second pause indicates paragraph break
                        is_end_of_paragraph = True
                else:
                    is_end_of_paragraph = True  # Last segment
                
                if is_end_of_paragraph and current_paragraph:
                    start_ms = int(current_start * 1000)
                    end_ms = int(segment['end'] * 1000)
                    
                    # Extract audio segment
                    audio_segment = audio[start_ms:end_ms]
                    
                    # Combine text from all sentences in paragraph
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
            # Original time-based segmentation (30 seconds)
            segment_length_ms = 30000
            for i in range(0, len(audio), segment_length_ms):
                segment = audio[i:i + segment_length_ms]
                segments.append({
                    'audio': segment,
                    'start_time': i / 1000.0,
                    'end_time': min((i + segment_length_ms) / 1000.0, len(audio) / 1000.0),
                    'text': '',
                    'type': 'time',
                    'duration': (segment_length_ms / 1000.0) # Add duration for time-based segments
                })
        
        return segments
    except Exception as e:
        print(f"Error in intelligent segmentation: {e}")
        return []

def segment_audio(audio_path, segment_length_ms=30000):
    """Segment audio into chunks"""
    try:
        audio = AudioSegment.from_wav(audio_path)
        segments = []
        
        for i in range(0, len(audio), segment_length_ms):
            segment = audio[i:i + segment_length_ms]
            segments.append(segment)
        
        return segments
    except Exception as e:
        print(f"Error segmenting audio: {e}")
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

def generate_tts_kokei_csv(results):
    """Generate CSV file in TTS Kokei training format"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # TTS Kokei CSV format: audio_path|text|speaker_id
        # Header (optional, but helpful)
        writer.writerow(['audio_path', 'text', 'speaker_id'])
        
        for result in results:
            if result['status'] == 'success' and result.get('transcription'):
                # Full audio file entry
                if result['transcription'].get('text'):
                    writer.writerow([
                        result['wav_path'],
                        result['transcription']['text'].strip(),
                        'speaker_1'  # Default speaker ID
                    ])
                
                # Segment entries
                for segment in result.get('segments', []):
                    if segment.get('transcription') and segment['transcription'].get('text'):
                        writer.writerow([
                            segment['path'],
                            segment['transcription']['text'].strip(),
                            'speaker_1'  # Default speaker ID
                        ])
        
        csv_content = output.getvalue()
        output.close()
        return csv_content
    except Exception as e:
        print(f"Error generating CSV: {e}")
        return None

def assess_audio_quality(audio_path):
    """Assess audio quality for transcription and voice cloning"""
    try:
        # Load audio with librosa
        y, sr = librosa.load(audio_path, sr=None)
        
        # Calculate various quality metrics
        
        # 1. Signal-to-Noise Ratio estimation
        # Calculate RMS energy
        rms = librosa.feature.rms(y=y)[0]
        rms_mean = np.mean(rms)
        
        # 2. Zero Crossing Rate (indicates noise level)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = np.mean(zcr)
        
        # 3. Spectral Centroid (indicates brightness/clarity)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_centroid_mean = np.mean(spectral_centroid)
        
        # 4. Duration check
        duration = len(y) / sr
        
        # 5. Sample rate check
        sample_rate = sr
        
        # Quality assessment logic
        quality_score = 0
        issues = []
        
        # Check sample rate (higher is better for voice cloning)
        if sample_rate >= 44100:
            quality_score += 25
        elif sample_rate >= 22050:
            quality_score += 15
            issues.append("Sample rate could be higher for optimal voice cloning")
        else:
            quality_score += 5
            issues.append("Low sample rate - not recommended for voice cloning")
        
        # Check RMS energy (signal strength)
        if rms_mean > 0.01:
            quality_score += 25
        elif rms_mean > 0.005:
            quality_score += 15
            issues.append("Signal level is low")
        else:
            quality_score += 5
            issues.append("Very low signal level - may affect transcription quality")
        
        # Check zero crossing rate (noise indicator)
        if zcr_mean < 0.1:
            quality_score += 25
        elif zcr_mean < 0.2:
            quality_score += 15
            issues.append("Moderate noise detected")
        else:
            quality_score += 5
            issues.append("High noise level detected")
        
        # Check duration (longer is better for voice cloning)
        if duration >= 60:  # 1 minute or more
            quality_score += 25
        elif duration >= 30:  # 30 seconds or more
            quality_score += 20
        elif duration >= 10:  # 10 seconds or more
            quality_score += 15
        else:
            quality_score += 5
            issues.append("Short duration - may not be suitable for voice cloning")
        
        # Determine suitability
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

@audio_bp.route('/upload', methods=['POST'])
def upload_files():
    """Handle multiple file uploads with segmentation options"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    # Get segmentation type from form data (default to 'sentence')
    segmentation_type = request.form.get('segmentation_type', 'sentence')
    
    results = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Generate unique filename
            file_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            
            # Create temporary directory for this file
            temp_dir = tempfile.mkdtemp()
            original_path = os.path.join(temp_dir, filename)
            wav_path = os.path.join(temp_dir, f"{file_id}.wav")
            
            try:
                # Save uploaded file
                file.save(original_path)
                
                # Convert to WAV
                if convert_to_wav(original_path, wav_path):
                    # Assess quality
                    quality_assessment = assess_audio_quality(wav_path)
                    
                    # Segment audio if quality is sufficient
                    segments_info = []
                    transcription_result = None
                    
                    if quality_assessment['transcription_suitable']:
                        # Transcribe the full audio first
                        transcription_result = transcribe_audio(wav_path)
                        
                        # Use intelligent segmentation based on transcription
                        if transcription_result and transcription_result.get('segments'):
                            intelligent_segments = segment_audio_intelligent(
                                wav_path, transcription_result, segmentation_type
                            )
                            
                            for i, segment_data in enumerate(intelligent_segments):
                                segment_path = os.path.join(temp_dir, f"{file_id}_segment_{i}_{segmentation_type}.wav")
                                segment_data['audio'].export(segment_path, format="wav")
                                
                                segments_info.append({
                                    'segment_id': i,
                                    'path': segment_path,
                                    'start_time': segment_data['start_time'],
                                    'end_time': segment_data['end_time'],
                                    'duration': segment_data['end_time'] - segment_data['start_time'],
                                    'text': segment_data['text'],
                                    'type': segment_data['type'],
                                    'transcription': {
                                        'text': segment_data['text'],
                                        'language': transcription_result.get('language', 'unknown')
                                    }
                                })
                        else:
                            # Fallback to time-based segmentation if transcription fails
                            segments = segment_audio(wav_path)
                            
                            for i, segment in enumerate(segments):
                                segment_path = os.path.join(temp_dir, f"{file_id}_segment_{i}_time.wav")
                                segment.export(segment_path, format="wav")
                                
                                # Transcribe each segment
                                segment_transcription = transcribe_audio(segment_path)
                                
                                segments_info.append({
                                    'segment_id': i,
                                    'path': segment_path,
                                    'duration': len(segment) / 1000.0,
                                    'type': 'time',
                                    'transcription': segment_transcription
                                })
                    
                    results.append({
                        'file_id': file_id,
                        'original_filename': filename,
                        'wav_path': wav_path,
                        'quality_assessment': quality_assessment,
                        'transcription': transcription_result,
                        'segments': segments_info,
                        'segmentation_type': segmentation_type,
                        'status': 'success'
                    })
                else:
                    results.append({
                        'file_id': file_id,
                        'original_filename': filename,
                        'status': 'error',
                        'error': 'Failed to convert to WAV format'
                    })
                    
            except Exception as e:
                results.append({
                    'file_id': file_id,
                    'original_filename': filename,
                    'status': 'error',
                    'error': str(e)
                })
        else:
            results.append({
                'original_filename': file.filename,
                'status': 'error',
                'error': 'File type not allowed'
            })
    
    return jsonify({'results': results})

@audio_bp.route('/transcribe/<file_id>', methods=['POST'])
def transcribe_file(file_id):
    """Transcribe a specific file"""
    # This endpoint can be used to re-transcribe or transcribe with different settings
    return jsonify({'message': 'Transcription endpoint for specific file'})

@audio_bp.route('/quality/<file_id>', methods=['GET'])
def get_quality_assessment(file_id):
    """Get quality assessment for a specific file"""
    # This would typically retrieve from a database or cache
    # For now, return a placeholder response
    return jsonify({'message': 'Quality assessment endpoint'})

@audio_bp.route('/export/csv', methods=['POST'])
def export_csv():
    """Export processing results as CSV for TTS Kokei training"""
    try:
        # Get results from request body
        data = request.get_json()
        if not data or 'results' not in data:
            return jsonify({'error': 'No results provided'}), 400
        
        results = data['results']
        csv_content = generate_tts_kokei_csv(results)
        
        if csv_content is None:
            return jsonify({'error': 'Failed to generate CSV'}), 500
        
        # Create response with CSV content
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=tts_kokei_training_data.csv'
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@audio_bp.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """Download processed audio file"""
    # This would typically retrieve the file path from a database
    # For now, return a placeholder response
    return jsonify({'message': 'Download endpoint'})



@audio_bp.route("/status", methods=["GET"])
def audio_status():
    return jsonify({"status": "Audio API is running"})


