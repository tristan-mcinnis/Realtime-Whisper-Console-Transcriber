# Realtime Whisper Console Transcriber (Refreshed)

A simple, fast terminal transcriber with two commands:

* `live` – real-time microphone transcription  
* `diarize` – offline speaker diarization (optional)

`live` defaults to the low-latency RealtimeSTT engine and automatically falls back to a legacy SpeechRecognition + faster-whisper path if RealtimeSTT is not installed.  
`diarize` uses the Senko library for very fast speaker diarization when available.

---

## 1&nbsp;· Features
- **Live mic transcription in terminal**
- **Default engine**: RealtimeSTT (voice-activity-detection, wake-word ready, low latency)  
  **Fallback**: legacy SpeechRecognition + faster-whisper
- **Optional offline speaker diarization** via Senko (`diarize` command)
- Saves transcripts to `~/Downloads/` automatically (disable with `--no-save`)
- Tested on **macOS** and **Windows**

---

## 2&nbsp;· Requirements
- Python **3.9+**
- **PortAudio** runtime for microphone access  
  • macOS: `brew install portaudio` then `pip install pyaudio`  
  • Windows: `pip install pipwin && pipwin install pyaudio`

---

## 3&nbsp;· Install

```bash
git clone https://github.com/tristan-mcinnis/Realtime-Whisper-Console-Transcriber
cd Realtime-Whisper-Console-Transcriber

# create & activate virtual env  (Windows: .venv\Scripts\activate)
python -m venv .venv && source .venv/bin/activate

# core dependencies
pip install -r requirements.txt

# Optional – best live experience
pip install RealtimeSTT

# Optional – diarization (Senko)
# mac / CPU:
uv pip install "git+https://github.com/narcotic-sh/senko.git"
# NVIDIA GPU: see Senko README for the correct extras
```

---

## 4&nbsp;· Usage

### Live (default engine: RealtimeSTT)
```bash
python transcribe.py live --language en
```
If RealtimeSTT is not present, the script transparently switches to the legacy engine.

```bash
# Minimal console output (no Rich panels)
python transcribe.py live --language en --plain
```

### Live with legacy engine
```bash
python transcribe.py live --engine legacy \
    --language en \
    --buffer-size 2 \
    --phrase-time-limit 3
```

### Diarize a WAV file (16 kHz mono 16-bit)
```bash
python transcribe.py diarize path/to/audio.wav \
    --device auto \
    --json-out diarization.json
```
Prints speaker segments and (optionally) writes merged segments to JSON.  
Prepare audio with `ffmpeg -i input.mp3 -ac 1 -ar 16000 -sample_fmt s16 output.wav`  (if you pass a non-WAV file, the tool will attempt this conversion automatically when **ffmpeg** is available).

---

## 5&nbsp;· Notes
- **GPU** acceleration is optional. RealtimeSTT supports CUDA; faster-whisper runs on CPU by default.
- On **Windows**, multiprocessing requirements are handled inside the script (`if __name__ == "__main__":` guard).
- Disable automatic saving of transcripts via `--no-save` flag on `live`.

---

## 6&nbsp;· License
This project remains under the existing LICENSE contained in the repository.
