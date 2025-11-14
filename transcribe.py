import os
import sys
import time
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import shutil
import subprocess
import tempfile

# Set the environment variable to allow duplicate OpenMP runtime initialization
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from rich.console import Console
from rich.panel import Panel

# Initialize Rich Console
console = Console()

def save_log_to_file(lines: List[str], prefix: str = "transcript") -> str:
    """Writes joined lines with newlines to ~/Downloads/{prefix}-{YYYYMMDD-HHMMSS}.txt"""
    downloads_folder = str(Path.home() / "Downloads")
    filename = f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    file_path = os.path.join(downloads_folder, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    console.print(Panel(f"Transcript saved to {file_path}", border_style="green", title="OUTPUT"))
    return file_path

def fmt_ts(seconds: float) -> str:
    """Format seconds to HH:MM:SS.mmm"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{seconds:.3f}"

def ensure_wav_16k_mono(input_path: str) -> str:
    """
    Ensure the provided file is a 16 kHz mono 16-bit WAV.
    If the file is already a .wav we optimistically assume it is correct.
    Otherwise we attempt conversion via ffmpeg, writing to a temp file.
    """
    # fast-path for wav
    if input_path.lower().endswith('.wav'):
        return input_path

    ff = shutil.which('ffmpeg')
    if not ff:
        raise RuntimeError(
            "Non-WAV file provided and ffmpeg not found. "
            "Please convert the audio to 16 kHz mono 16-bit WAV or install ffmpeg."
        )

    tmp_out = os.path.join(
        tempfile.gettempdir(), f"diarize-{int(time.time())}.wav"
    )
    cmd = [
        ff,
        '-y',
        '-i', input_path,
        '-ac', '1',
        '-ar', '16000',
        '-sample_fmt', 's16',
        tmp_out,
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(
            f"ffmpeg conversion failed: {res.stderr.decode(errors='ignore')[:400]}"
        )
    return tmp_out

def live_realtimestt(language: str, model: str, save: bool, plain: bool = False) -> None:
    try:
        from RealtimeSTT import AudioToTextRecorder
    except Exception:
        raise ImportError("RealtimeSTT not installed. Install with: pip install RealtimeSTT")

    captured: List[str] = []

    def append_and_print(text: str):
        if not text:
            return
        console.print(text)
        captured.append(text)

    # Use VAD-driven segments; print final phrases for stability and simplicity
    try:
        with AudioToTextRecorder(
            model=model,
            language=language or "auto",
            enable_realtime_transcription=False,
        ) as recorder:
            if plain:
                console.print("Listening… Press CTRL+C to stop")
            else:
                console.print(Panel("Listening… Press CTRL+C to stop", border_style="green", title="LIVE · RealtimeSTT"))
            recorder.listen()
            while True:
                phrase = recorder.text()  # blocks until a phrase is finalized by VAD
                append_and_print(phrase)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(Panel(f"RealtimeSTT error: {e}", border_style="red", title="ERROR"))
    finally:
        # Best-effort shutdown if context wasn't used or was interrupted
        try:
            recorder.shutdown()  # type: ignore[name-defined]
        except Exception:
            pass
        if save and captured:
            save_log_to_file(captured, prefix="live")

def live_legacy(language: str, model: str, buffer_size: int, phrase_time_limit: int, save: bool, plain: bool = False) -> None:
    try:
        import speech_recognition as sr
    except Exception as e:
        console.print(Panel("speech_recognition is required for legacy mode. Install with: pip install SpeechRecognition", border_style="red", title="MISSING DEP"))
        return
    try:
        from faster_whisper import WhisperModel
    except Exception:
        console.print(Panel("faster-whisper is required for legacy mode. Install with: pip install faster-whisper", border_style="red", title="MISSING DEP"))
        return

    num_cores = max(1, (os.cpu_count() or 2) // 2)
    whisper_model = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=num_cores, num_workers=num_cores)

    r = sr.Recognizer()
    buffer: List[str] = []
    captured: List[str] = []

    def wav_to_text(audio_path: str, lang: str) -> str:
        segments, _ = whisper_model.transcribe(audio_path, language=lang)
        return ''.join(seg.text for seg in segments)

    def callback(recognizer, audio):
        nonlocal buffer
        tmp_path = 'prompt.wav'
        try:
            with open(tmp_path, 'wb') as f:
                f.write(audio.get_wav_data())
            text = wav_to_text(tmp_path, language)
            buffer.append(text)
            if len(buffer) >= buffer_size:
                combined = ' '.join(buffer)
                console.print(combined)
                captured.append(combined)
                buffer = []
        except Exception as e:
            console.print(Panel(f"Legacy callback error: {e}", border_style="red", title="ERROR"))
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    # ambient noise adjust and background listen
    try:
        with sr.Microphone() as source:
            if plain:
                console.print(f"Adjusting for ambient noise… (Language: {language})")
            else:
                console.print(Panel(f"Adjusting for ambient noise… (Language: {language})", border_style="blue", title="INIT"))
            r.adjust_for_ambient_noise(source, duration=2)
        if plain:
            console.print("Start speaking. Press CTRL+C to stop")
        else:
            console.print(Panel("Start speaking. Press CTRL+C to stop", border_style="green", title="LIVE · Legacy"))
        stop_listening = r.listen_in_background(sr.Microphone(), callback, phrase_time_limit=phrase_time_limit)
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        try:
            stop_listening(wait_for_stop=False)
        except Exception:
            pass
    except Exception as e:
        console.print(Panel(f"Legacy runtime error: {e}", border_style="red", title="ERROR"))
    finally:
        # flush remaining buffer
        if buffer:
            combined = ' '.join(buffer)
            console.print(combined)
            captured.append(combined)
            buffer = []
        if save and captured:
            save_log_to_file(captured, prefix="live")

def diarize_file(audio_path: str, device: str = 'auto', json_out: Optional[str] = None) -> None:
    try:
        import senko
    except Exception:
        console.print(Panel(
            "Senko not installed. Install (Mac/CPU):\n  uv pip install 'git+https://github.com/narcotic-sh/senko.git'\nFor NVIDIA CUDA: see Senko README",
            border_style="yellow", title="OPTIONAL DEP"
        ))
        return

    src = ensure_wav_16k_mono(audio_path)
    try:
        diarizer = senko.Diarizer(torch_device=device, warmup=True, quiet=True)
        result = diarizer.diarize(src, generate_colors=False)
        if result is None:
            console.print(Panel("No speakers detected.", border_style="yellow", title="DIARIZATION"))
            return
        segments = result.get("merged_segments", [])
        console.print(Panel(f"Detected {len({seg['speaker'] for seg in segments}) if segments else 0} speakers; {len(segments)} segments", border_style="green", title="DIARIZATION"))
        for seg in segments:
            s = seg.get('start', 0.0)
            e = seg.get('end', 0.0)
            spk = seg.get('speaker', '?')
            console.print(f"[{fmt_ts(s)} – {fmt_ts(e)}] {spk}")
        if json_out:
            with open(json_out, 'w', encoding='utf-8') as f:
                json.dump({"merged_segments": segments}, f, indent=2)
            console.print(Panel(f"Saved JSON: {json_out}", border_style="green", title="OUTPUT"))
    except Exception as e:
        console.print(Panel(f"Diarization error: {e}", border_style="red", title="ERROR"))
    finally:
        # remove temp converted file if we created one
        try:
            if src != audio_path and os.path.exists(src):
                os.remove(src)
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser(description="Console transcriber: realtime (live) and diarization (offline)")
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_live = sub.add_parser('live', help='Real-time microphone transcription')
    p_live.add_argument('--engine', choices=['rstt', 'legacy'], default='rstt', help='Transcription engine (default: rstt)')
    p_live.add_argument('--language', default='en', help='Language code (e.g., en, es, zh). Use empty for auto')
    p_live.add_argument('--model', default='base', help='Whisper model size/name (e.g., tiny, base, small)')
    p_live.add_argument('--buffer-size', type=int, default=2, help='Legacy engine: number of segments to buffer before printing')
    p_live.add_argument('--phrase-time-limit', type=int, default=3, help='Legacy engine: seconds per phrase chunk')
    p_live.add_argument('--no-save', action='store_true', help='Do not save transcript to Downloads at exit')
    p_live.add_argument('--plain', action='store_true', help='Plain output (no rich panels)')

    p_diar = sub.add_parser('diarize', help='Offline speaker diarization for an audio file (WAV 16kHz mono)')
    p_diar.add_argument('audio_path', help='Path to WAV file (16kHz mono 16-bit)')
    p_diar.add_argument('--device', choices=['auto', 'cuda', 'mps', 'cpu'], default='auto', help='Torch device for Senko (default: auto)')
    p_diar.add_argument('--json-out', default=None, help='Optional path to save merged segments JSON')

    args = parser.parse_args()

    if args.cmd == 'live':
        save = not args.no_save
        if args.engine == 'rstt':
            try:
                live_realtimestt(args.language, args.model, save, args.plain)
            except ImportError as e:
                console.print(Panel(str(e) + "\nFalling back to legacy engine…", border_style="yellow", title="FALLBACK"))
                live_legacy(args.language, args.model, args.buffer_size, args.phrase_time_limit, save, args.plain)
        else:
            live_legacy(args.language, args.model, args.buffer_size, args.phrase_time_limit, save, args.plain)
    elif args.cmd == 'diarize':
        diarize_file(args.audio_path, device=args.device, json_out=args.json_out)

if __name__ == '__main__':
    main()
