import os
import time
from datetime import datetime
from pathlib import Path

# Set the environment variable to allow duplicate OpenMP runtime initialization
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from faster_whisper import WhisperModel
import speech_recognition as sr
from rich.console import Console
from rich.panel import Panel

# Initialize Rich Console
console = Console()

# Initialize Whisper model
num_cores = os.cpu_count()
whisper_model = WhisperModel('base', device='cpu', compute_type='int8', cpu_threads=num_cores // 2, num_workers=num_cores // 2)

r = sr.Recognizer()

buffer = []
buffer_size = 2  # Number of segments to buffer before printing

# To capture console output
captured_output = []

def log(message):
    if isinstance(message, Panel):
        console.print(message)
    else:
        console.print(message)
        captured_output.append(message)

def wav_to_text(audio_path, language):
    segments, _ = whisper_model.transcribe(audio_path, language=language)
    text = ''.join(segment.text for segment in segments)
    return text

def callback(recognizer, audio, language):
    global buffer
    prompt_audio_path = 'prompt.wav'
    with open(prompt_audio_path, 'wb') as f:
        f.write(audio.get_wav_data())
    prompt_text = wav_to_text(prompt_audio_path, language)
    buffer.append(prompt_text)
    if len(buffer) >= buffer_size:
        combined_text = ' '.join(buffer)
        log(combined_text)
        buffer = []

def save_log_to_file(text):
    downloads_folder = str(Path.home() / "Downloads")
    filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt"
    file_path = os.path.join(downloads_folder, filename)
    with open(file_path, 'w') as f:
        f.write(text)
    log(Panel(f"Transcription saved to {file_path}", border_style="bold green", title="LOG"))

def start_listening(language='en'):
    log(Panel(f"Adjusting for ambient noise... (Language: {language})", border_style="blue1", title="ACTION"))
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=2)
    log(Panel("Start speaking / start audio. Press 'CTRL + C' to exit", border_style="green1", title="ACTION"))
    stop_listening = r.listen_in_background(sr.Microphone(), lambda recognizer, audio: callback(recognizer, audio, language), phrase_time_limit=3)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_listening(wait_for_stop=False)
        combined_text = '\n'.join(str(msg) for msg in captured_output if not isinstance(msg, Panel))
        save_log_to_file(combined_text)
        log(Panel("Listening stopped.", border_style="magenta3", title="ACTION"))

if __name__ == "__main__":
    # Prompt user to input the language code
    console.print(Panel("Please enter the language code (e.g., 'en' for English, 'zh' for Simplified Chinese, 'es' for Spanish):", border_style="bold purple", title="LANGUAGE SELECTION"))
    language_code = input("Enter language code: ").strip()
    start_listening(language_code)
