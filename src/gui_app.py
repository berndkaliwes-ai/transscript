import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import json
import shutil
import tempfile
from audio_processor import convert_to_wav, assess_audio_quality, transcribe_audio, segment_audio_intelligent, get_whisper_model


class WhatsAppVoiceProcessorGUI:
    def __init__(self, master):
        self.master = master
        master.title("WhatsApp Voice Processor")
        master.geometry("800x600")

        self.files = []
        self.segmentation_type = tk.StringVar(value="sentence")

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Upload Section
        upload_frame = ttk.LabelFrame(main_frame, text="Dateien hochladen", padding="10")
        upload_frame.pack(fill=tk.X, pady=5)

        self.file_list_label = ttk.Label(upload_frame, text="Keine Dateien ausgewählt.")
        self.file_list_label.pack(pady=5)

        select_button = ttk.Button(upload_frame, text="Dateien auswählen", command=self.select_files)
        select_button.pack(pady=5)

        # Segmentation Options
        segmentation_frame = ttk.LabelFrame(main_frame, text="Segmentierungsart wählen", padding="10")
        segmentation_frame.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(segmentation_frame, text="Sätze (empfohlen)", variable=self.segmentation_type, value="sentence").pack(anchor=tk.W)
        ttk.Radiobutton(segmentation_frame, text="Absätze", variable=self.segmentation_type, value="paragraph").pack(anchor=tk.W)
        ttk.Radiobutton(segmentation_frame, text="Zeitbasiert (30s)", variable=self.segmentation_type, value="time").pack(anchor=tk.W)

        # Process Button
        self.process_button = ttk.Button(main_frame, text="Dateien verarbeiten", command=self.process_files, state=tk.DISABLED)
        self.process_button.pack(pady=10)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=5)

        # Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Verarbeitungsergebnisse", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.results_text = tk.Text(results_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.results_text.pack(fill=tk.BOTH, expand=True)

    def select_files(self):
        selected_files = filedialog.askopenfilenames(
            title="Wählen Sie Audiodateien aus",
            filetypes=(
                ("Audio files", "*.mp3 *.wav *.opus *.ogg *.flac *.m4a *.aac *.wma"),
                ("All files", "*.*")
            )
        )
        if selected_files:
            self.files = list(selected_files)
            self.file_list_label.config(text=f"{len(self.files)} Dateien ausgewählt.")
            self.process_button.config(state=tk.NORMAL)
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Bereit zur Verarbeitung...\n")
            self.results_text.config(state=tk.DISABLED)
        else:
            self.file_list_label.config(text="Keine Dateien ausgewählt.")
            self.process_button.config(state=tk.DISABLED)

    def process_files(self):
        if not self.files:
            messagebox.showwarning("Keine Dateien", "Bitte wählen Sie zuerst Audiodateien aus.")
            return

        self.process_button.config(state=tk.DISABLED)
        self.results_text.config(state=tk.NORMAL)
        # ZIP-Download Button
        self.zip_button = ttk.Button(main_frame, text="Ergebnisse als ZIP herunterladen", command=self.zip_results, state=tk.NORMAL)
        self.zip_button.pack(pady=5)
        self.results_text.delete(1.0, tk.END)
    def zip_results(self):
        import zipfile
        from tkinter import filedialog, messagebox
        result_dirs = []
        for file_path in self.files:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            result_dir = os.path.join(os.path.dirname(file_path), base_name)
            if os.path.exists(result_dir):
                result_dirs.append(result_dir)

        if not result_dirs:
            messagebox.showinfo("Keine Ergebnisse", "Es wurden keine Ergebnisordner gefunden.")
            return

        zip_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            title="Speicherort für ZIP wählen"
        )
        if not zip_path:
            return

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for result_dir in result_dirs:
                for root, _, files in os.walk(result_dir):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        rel_path = os.path.relpath(abs_path, os.path.dirname(zip_path))
                        zipf.write(abs_path, rel_path)
        messagebox.showinfo("ZIP erstellt", f"ZIP-Datei gespeichert: {zip_path}")
        self.results_text.insert(tk.END, "Verarbeitung gestartet...\n")
        self.results_text.config(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = len(self.files)

        # Run processing in a separate thread to keep GUI responsive
        threading.Thread(target=self._process_files_thread).start()

    def _process_files_thread(self):
        all_results = []
        get_whisper_model() # Load model once
        for i, file_path in enumerate(self.files):
            self.update_status(f"Verarbeite Datei {i+1}/{len(self.files)}: {os.path.basename(file_path)}")
            temp_dir = os.path.join(tempfile.gettempdir(), f"audio_processing_{os.getpid()}_{i}")
            os.makedirs(temp_dir, exist_ok=True)
            try:
                wav_output_path = os.path.join(temp_dir, os.path.basename(file_path).rsplit(".", 1)[0] + ".wav")
                if not convert_to_wav(file_path, wav_output_path):
                    raise Exception("WAV conversion failed")

                quality_assessment = assess_audio_quality(wav_output_path)
                transcription_result = transcribe_audio(wav_output_path)
                segments = segment_audio_intelligent(wav_output_path, transcription_result, self.segmentation_type.get())


                # Ergebnisse speichern
                from audio_processor import save_segments_and_csv
                error_list = quality_assessment.get("issues", [])
                result_dir, csv_path = save_segments_and_csv(
                    original_filename=file_path,
                    wav_path=wav_output_path,
                    segments=segments,
                    error_list=error_list
                )

                result = {
                    "original_filename": os.path.basename(file_path),
                    "status": "success",
                    "quality_assessment": quality_assessment,
                    "transcription": transcription_result,
                    "segments": [{
                        "start_time": s["start_time"],
                        "end_time": s["end_time"],
                        "text": s["text"],
                        "type": s["type"]
                    } for s in segments],
                    "result_dir": result_dir,
                    "csv_path": csv_path
                }
                all_results.append(result)

            except Exception as e:
                result = {
                    "original_filename": os.path.basename(file_path),
                    "status": "error",
                    "error": str(e)
                }
                all_results.append(result)
                self.update_status(f"Fehler bei {os.path.basename(file_path)}: {e}")
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                self.progress_bar["value"] = i + 1
        
        self.display_results(all_results)
        self.process_button.config(state=tk.NORMAL)
        self.update_status("Verarbeitung abgeschlossen.")

    def update_status(self, message):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, f"{message}\n")
        self.results_text.see(tk.END) # Scroll to the end
        self.results_text.config(state=tk.DISABLED)

    def display_results(self, all_results):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, "\n--- Endergebnisse ---\n")
        for res in all_results:
            self.results_text.insert(tk.END, f"Datei: {res['original_filename']}\n")
            self.results_text.insert(tk.END, f"Status: {res['status']}\n")
            if res['status'] == 'success':
                self.results_text.insert(tk.END, f"  Transkription: {res['transcription']['text'][:50]}...\n")
                self.results_text.insert(tk.END, f"  Qualitätsscore: {res['quality_assessment']['quality_score']}\n")
                self.results_text.insert(tk.END, f"  Segmente gefunden: {len(res['segments'])}\n")
            else:
                self.results_text.insert(tk.END, f"  Fehler: {res['error']}\n")
            self.results_text.insert(tk.END, "\n")
        self.results_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = WhatsAppVoiceProcessorGUI(root)
    root.mainloop()

