
import pytest
import os
import tempfile
from pydub import AudioSegment
from src.routes.audio import convert_to_wav, segment_audio_intelligent, assess_audio_quality, transcribe_audio, generate_tts_kokei_csv, allowed_file
from pydub.generators import Sine

# Create a dummy audio file for testing
@pytest.fixture(scope="module")
def dummy_audio_file():
    # Create a short, simple WAV file
    sample_rate = 44100
    duration_ms = 5000  # 5 seconds
    channels = 1
    sample_width = 2
    
    # Generate a simple sine wave
    sine_wave = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate).set_channels(1).set_sample_width(sample_width)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
        sine_wave.export(fp.name, format="wav")
        file_path = fp.name
    yield file_path
    os.unlink(file_path)

@pytest.fixture(scope="module")
def dummy_opus_file():
    # Create a short, simple OPUS file (requires ffmpeg/libav)
    # For simplicity, we'll convert the dummy WAV to OPUS
    sample_rate = 44100
    duration_ms = 5000  # 5 seconds
    sample_width = 2
    sine_wave = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate).set_channels(1).set_sample_width(sample_width)
    
    with tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as fp:
        sine_wave.export(fp.name, format="opus")
        file_path = fp.name
    yield file_path
    os.unlink(file_path)


def test_convert_to_wav(dummy_opus_file):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
        output_path = fp.name
    
    success = convert_to_wav(dummy_opus_file, output_path)
    assert success is True
    assert os.path.exists(output_path)
    
    audio = AudioSegment.from_wav(output_path)
    assert audio.frame_rate == 44100
    assert audio.sample_width == 2
    os.unlink(output_path)

def test_assess_audio_quality(dummy_audio_file):
    quality_assessment = assess_audio_quality(dummy_audio_file)
    assert isinstance(quality_assessment, dict)
    assert "quality_score" in quality_assessment
    assert quality_assessment["quality_score"] > 0
    assert "transcription_suitable" in quality_assessment
    assert "voice_cloning_suitable" in quality_assessment

def test_transcribe_audio(dummy_audio_file):
    # Note: Whisper needs to download its model on first run, which can be slow.
    # For a dummy sine wave, transcription will likely be empty or gibberish, but the function should run.
    transcription_result = transcribe_audio(dummy_audio_file)
    assert isinstance(transcription_result, dict)
    assert "text" in transcription_result
    assert "language" in transcription_result
    assert "segments" in transcription_result

def test_segment_audio_intelligent_sentence(dummy_audio_file):
    # For a dummy sine wave, transcription segments will be empty, so we mock them
    mock_transcription = {
        "text": "This is a test sentence. This is another one.",
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "This is a test sentence."},
            {"start": 2.5, "end": 4.5, "text": "This is another one."}
        ]
    }
    segments = segment_audio_intelligent(dummy_audio_file, mock_transcription, "sentence")
    assert len(segments) == 2
    assert segments[0]["type"] == "sentence"
    assert segments[0]["text"] == "This is a test sentence."
    assert segments[1]["text"] == "This is another one."

def test_segment_audio_intelligent_paragraph(dummy_audio_file):
    mock_transcription = {
        "text": "First paragraph. Second sentence. Third sentence. Another paragraph.",
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 1.0, "text": "First paragraph."}, # Segment 1
            {"start": 1.5, "end": 2.0, "text": "Second sentence."}, # Segment 2
            {"start": 2.5, "end": 3.0, "text": "Third sentence."}, # Segment 3
            {"start": 5.5, "end": 6.5, "text": "Another paragraph."} # Segment 4 (long pause before this)
        ]
    }
    segments = segment_audio_intelligent(dummy_audio_file, mock_transcription, "paragraph")
    assert len(segments) == 2 # Should group segments 1-3 and segment 4
    assert segments[0]["type"] == "paragraph"
    assert segments[0]["text"] == "First paragraph. Second sentence. Third sentence."
    assert segments[1]["text"] == "Another paragraph."

def test_segment_audio_intelligent_time(dummy_audio_file):
    mock_transcription = {"text": "", "language": "en", "segments": []}
    segments = segment_audio_intelligent(dummy_audio_file, mock_transcription, "time")
    assert len(segments) > 0
    assert segments[0]["type"] == "time"
    assert segments[0]["duration"] == pytest.approx(30.0, 0.1) # First segment should be ~30s





def test_convert_to_wav_error_handling():
    # Test with a non-existent file
    success = convert_to_wav("non_existent_file.mp3", "output.wav")
    assert success is False

def test_assess_audio_quality_error_handling():
    # Test with a non-existent file
    quality_assessment = assess_audio_quality("non_existent_file.wav")
    assert quality_assessment["quality_score"] == 0
    assert quality_assessment["transcription_suitable"] is False
    assert quality_assessment["voice_cloning_suitable"] is False
    assert len(quality_assessment["issues"]) > 0

def test_transcribe_audio_error_handling():
    # Test with a non-existent file
    transcription_result = transcribe_audio("non_existent_file.wav")
    assert transcription_result["text"] == ""
    assert transcription_result["language"] == "unknown"
    assert transcription_result["error"] is not None

def test_generate_tts_kokei_csv():
    mock_results = [
        {
            "status": "success",
            "file_id": "1",
            "original_filename": "test1.wav",
            "wav_path": "/tmp/test1.wav",
            "transcription": {
                "text": "Hello world.",
                "language": "en",
                "segments": [
                    {"start": 0.0, "end": 1.0, "text": "Hello"},
                    {"start": 1.1, "end": 2.0, "text": "world."}
                ]
            },
            "segments": [
                {
                    "segment_id": 0,
                    "path": "/tmp/test1_segment_0.wav",
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "duration": 2.0,
                    "text": "Hello world.",
                    "type": "sentence",
                    "transcription": {"text": "Hello world.", "language": "en"}
                }
            ]
        },
        {
            "status": "error",
            "original_filename": "test2.mp3",
            "error": "File type not allowed"
        }
    ]
    csv_content = generate_tts_kokei_csv(mock_results)
    assert csv_content is not None
    assert "audio_path,text,speaker_id" in csv_content
    assert "/tmp/test1.wav,Hello world.,speaker_1" in csv_content
    assert "/tmp/test1_segment_0.wav,Hello world.,speaker_1" in csv_content
    assert "test2.mp3" not in csv_content




def test_allowed_file():
    assert allowed_file("audio.mp3") is True
    assert allowed_file("audio.wav") is True
    assert allowed_file("audio.opus") is True
    assert allowed_file("audio.ogg") is True
    assert allowed_file("audio.flac") is True
    assert allowed_file("audio.m4a") is True
    assert allowed_file("audio.aac") is True
    assert allowed_file("audio.wma") is True
    assert allowed_file("document.pdf") is False
    assert allowed_file("image.jpg") is False
    assert allowed_file("no_extension") is False
    assert allowed_file(".mp3") is False





from src.main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_upload_files_no_files(client):
    response = client.post("/api/audio/upload")
    assert response.status_code == 400
    assert "No files provided" in response.json["error"]

def test_upload_files_empty_files(client):
    data = {"files": []}
    response = client.post("/api/audio/upload", data=data)
    assert response.status_code == 400
    assert "No files provided" in response.json["error"]

# More tests will be added here to reach 90% coverage




def test_upload_files_success(client, dummy_audio_file):
    with open(dummy_audio_file, 'rb') as f:
        data = {
            'files': [(f, 'test_audio.wav')],
            'segmentation_type': 'sentence'
        }
        response = client.post('/api/audio/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    assert 'results' in response.json
    assert len(response.json['results']) == 1
    result = response.json['results'][0]
    assert result['status'] == 'success'
    assert 'wav_path' in result
    assert 'quality_assessment' in result
    assert 'transcription' in result
    assert 'segments' in result
    assert result['segmentation_type'] == 'sentence'





def test_main_app_config():
    assert app.config["SECRET_KEY"] == "asdf#FGSgvasgf$5$WGT"
    # UPLOAD_FOLDER is set in main.py, but not directly accessible via app.config in this test context
    # assert app.config["UPLOAD_FOLDER"] == "uploads" # Skipping for now
    assert app.config["MAX_CONTENT_LENGTH"] == 100 * 1024 * 1024

def test_main_app_routes():
    # Check if blueprints are registered
    assert "audio" in app.blueprints
    assert "user" in app.blueprints
    # Check a few specific routes
    with app.test_client() as client:
        response = client.get("/api/audio/status")
        assert response.status_code == 200
        assert response.get_json() == {"status": "Audio API is running"}

        response = client.get("/api/profile")
        assert response.status_code == 200
        assert response.get_json() == {"message": "User profile endpoint"}




def test_get_users(client):
    response = client.get("/api/users")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_create_user(client):
    data = {"username": "testuser", "email": "test@example.com"}
    response = client.post("/api/users", json=data)
    assert response.status_code == 201
    assert response.get_json()["username"] == "testuser"

def test_get_user(client):
    # First create a user to get an ID
    data = {"username": "tempuser", "email": "temp@example.com"}
    create_response = client.post("/api/users", json=data)
    user_id = create_response.get_json()["id"]

    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    assert response.get_json()["username"] == "tempuser"

def test_update_user(client):
    # First create a user to get an ID
    data = {"username": "updateuser", "email": "update@example.com"}
    create_response = client.post("/api/users", json=data)
    user_id = create_response.get_json()["id"]

    update_data = {"username": "updateduser", "email": "updated@example.com"}
    response = client.put(f"/api/users/{user_id}", json=update_data)
    assert response.status_code == 200
    assert response.get_json()["username"] == "updateduser"

def test_delete_user(client):
    # First create a user to get an ID
    data = {"username": "deleteuser", "email": "delete@example.com"}
    create_response = client.post("/api/users", json=data)
    user_id = create_response.get_json()["id"]

    response = client.delete(f"/api/users/{user_id}")
    assert response.status_code == 204

    # Verify user is deleted
    get_response = client.get(f"/api/users/{user_id}")
    assert get_response.status_code == 404


