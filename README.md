# Realtime Whisper Console Transcriber (WhisperLiveKit)

A minimal, real-time speech-to-text stack powered **entirely** by [WhisperLiveKit](https://github.com/QuentinFuxa/WhisperLiveKit).

## 1&nbsp;· Features
- 🔴 Live microphone transcription in the terminal  
- 🗣️ Optional **live speaker diarization**  
- 🖥️ Clean Electron desktop UI (auto-starts the backend)  
- 📂 Stream any audio/video file over WebSocket via CLI  

## 2&nbsp;· Requirements
- Python **3.9+**
- **ffmpeg** in `PATH`  
  • macOS `brew install ffmpeg` • Windows <https://ffmpeg.org/download.html>  
- Node **18+** (to run the optional Electron app)

## 3&nbsp;· Install
```bash
git clone https://github.com/tristan-mcinnis/Realtime-Whisper-Console-Transcriber
cd Realtime-Whisper-Console-Transcriber

# (optional) create & activate a virtual env
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate

# core deps – WhisperLiveKit, Rich, websockets, …
pip install -r requirements.txt
```

## 4&nbsp;· Usage

### ① Start a local server
```bash
python transcribe.py serve --language en --model base --diarization
# ↳ listens on ws://127.0.0.1:8801/asr
```
Speak and watch the transcript (with speaker labels if `--diarization` is passed) stream into the console.

### ② Desktop UI
```bash
cd electron
npm install           # first-time only
npm start
```
The UI launches, auto-spawns the server, connects the mic, and shows live text.

### ③ Stream a file to the server
```bash
python transcribe.py file path/to/audio_or_video.mp3 --url 127.0.0.1:8801
```
Results appear in the console and are saved to `~/Downloads/file-transcript-*.txt`.

---

## 5&nbsp;· License
This project remains under the original LICENSE.
