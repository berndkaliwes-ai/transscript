import unittest
from src.audio_processor import convert_to_wav, assess_audio_quality, transcribe_audio, segment_audio_intelligent, save_segments_and_csv
import os

class TestAudioProcessor(unittest.TestCase):
    def setUp(self):
        # Beispiel-Testdatei vorbereiten
        self.test_wav = os.path.join(os.path.dirname(__file__), 'test.wav')
        # Hier könnte eine kleine Dummy-WAV-Datei erzeugt werden
        # ...

    def test_convert_to_wav(self):
        # Test: Konvertierung funktioniert
        result = convert_to_wav(self.test_wav, 'out.wav')
        self.assertTrue(result)
        self.assertTrue(os.path.exists('out.wav'))

    def test_assess_audio_quality(self):
        # Test: Qualitätsbewertung liefert sinnvolle Werte
        result = assess_audio_quality(self.test_wav)
        self.assertIn('snr', result)
        self.assertIn('issues', result)

    def test_transcribe_audio(self):
        # Test: Transkription liefert Text
        result = transcribe_audio(self.test_wav)
        self.assertIsNotNone(result)
        self.assertIn('text', result)

    def test_segment_audio_intelligent(self):
        # Test: Segmentierung liefert Segmente
        transcription = transcribe_audio(self.test_wav)
        segments = segment_audio_intelligent(self.test_wav, transcription, 'sentence')
        self.assertIsInstance(segments, list)

    def test_save_segments_and_csv(self):
        # Test: Speicherung funktioniert
        transcription = transcribe_audio(self.test_wav)
        segments = segment_audio_intelligent(self.test_wav, transcription, 'sentence')
        result_dir, csv_path = save_segments_and_csv('test.wav', self.test_wav, segments)
        self.assertTrue(os.path.exists(result_dir))
        self.assertTrue(os.path.exists(csv_path))

if __name__ == '__main__':
    unittest.main()
