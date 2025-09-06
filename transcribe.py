#!/usr/bin/env python3
import os
import sys
import json
import shutil
import asyncio
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Set the environment variable to allow duplicate OpenMP runtime initialization
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from rich.console import Console
from rich.panel import Panel
import websockets

# Initialize Rich Console
console = Console()

def save_transcript(lines: List[str], prefix: str = "transcript") -> str:
    """Writes joined lines with newlines to ~/Downloads/{prefix}-{YYYYMMDD-HHMMSS}.txt"""
    downloads_folder = str(Path.home() / "Downloads")
    filename = f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    file_path = os.path.join(downloads_folder, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    console.print(Panel(f"Transcript saved to {file_path}", border_style="green", title="OUTPUT"))
    return file_path

def serve_command(args):
    """Run whisperlivekit-server with the specified arguments"""
    server_bin = shutil.which('whisperlivekit-server')
    if not server_bin:
        console.print(Panel(
            "whisperlivekit-server not found. Install with:\n  pip install whisperlivekit",
            border_style="red", title="ERROR"
        ))
        return 1
    
    cmd = [server_bin, '--host', args.host, '--port', str(args.port), 
           '--model', args.model, '--lan', args.language]
    
    if args.diarization:
        cmd.append('--diarization')
    
    # Add optional arguments if specified
    if args.device != 'auto':
        cmd.extend(['--device', args.device])
    
    if args.backend != 'simulstreaming':
        cmd.extend(['--backend', args.backend])
    
    console.print(Panel(
        f"Starting WhisperLiveKit server on {args.host}:{args.port}\n"
        f"Model: {args.model}, Language: {args.language}, Diarization: {'enabled' if args.diarization else 'disabled'}\n"
        f"Press Ctrl+C to stop",
        border_style="green", title="SERVER"
    ))
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True, 
            bufsize=1
        )
        
        # Stream output to console
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                console.print(line.rstrip())
                
    except KeyboardInterrupt:
        console.print(Panel("Stopping server...", border_style="yellow", title="SERVER"))
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    
    return 0

async def file_command(args):
    """Stream an audio file to the WhisperLiveKit server via WebSocket"""
    url = f"ws://{args.url}/asr"
    file_path = args.file
    
    if not os.path.exists(file_path):
        console.print(Panel(f"File not found: {file_path}", border_style="red", title="ERROR"))
        return 1
    
    console.print(Panel(
        f"Streaming file: {file_path}\nTo server: {url}\n",
        border_style="blue", title="FILE STREAMING"
    ))
    
    transcript_lines = []
    
    try:
        async with websockets.connect(url) as websocket:
            # Read and send file in chunks
            chunk_size = 64 * 1024  # 64KB chunks
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    await websocket.send(chunk)
                    await asyncio.sleep(0.01)  # Small delay to avoid flooding
                
                # Send empty chunk to signal end of audio
                await websocket.send(b'')
            
            console.print(Panel("File sent, waiting for transcription...", border_style="blue", title="PROCESSING"))
            
            # Receive and process responses
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Check if server is ready to stop
                    if data.get('type') == 'ready_to_stop':
                        break
                    
                    # Process and display lines
                    if 'lines' in data:
                        for line in data['lines']:
                            speaker = line.get('speaker', line.get('spk', ''))
                            text = line.get('text', line.get('line', ''))
                            
                            if speaker and text:
                                formatted_line = f"[{speaker}] {text}"
                                console.print(formatted_line)
                                transcript_lines.append(formatted_line)
                            elif text:
                                console.print(text)
                                transcript_lines.append(text)
                    else:
                        # Just print the raw JSON if we don't understand the format
                        console.print(json.dumps(data, indent=2))
                
                except websockets.exceptions.ConnectionClosed:
                    console.print(Panel("Connection closed by server", border_style="yellow", title="COMPLETE"))
                    break
                
    except websockets.exceptions.WebSocketException as e:
        console.print(Panel(f"WebSocket error: {e}", border_style="red", title="ERROR"))
        return 1
    except Exception as e:
        console.print(Panel(f"Error: {e}", border_style="red", title="ERROR"))
        return 1
    
    if transcript_lines:
        save_transcript(transcript_lines, prefix="file-transcript")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description="WhisperLiveKit Console Interface")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Command to run')
    
    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start WhisperLiveKit server')
    serve_parser.add_argument('--host', default='127.0.0.1', help='Host to bind server to (default: 127.0.0.1)')
    serve_parser.add_argument('--port', type=int, default=8801, help='Port to bind server to (default: 8801)')
    serve_parser.add_argument('--model', default='base', help='Whisper model size (default: base)')
    serve_parser.add_argument('--language', default='en', help='Language code (default: en, use "auto" for auto-detection)')
    serve_parser.add_argument('--diarization', action='store_true', help='Enable speaker diarization')
    serve_parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda', 'mps'], 
                             help='Device to use (default: auto)')
    serve_parser.add_argument('--backend', default='simulstreaming', 
                             choices=['simulstreaming', 'faster-whisper', 'whisper_timestamped', 'mlx-whisper'],
                             help='Backend to use (default: simulstreaming)')
    
    # File command
    file_parser = subparsers.add_parser('file', help='Stream audio file to WhisperLiveKit server')
    file_parser.add_argument('file', help='Path to audio file')
    file_parser.add_argument('--url', default='127.0.0.1:8801', help='Server URL (default: 127.0.0.1:8801)')
    
    args = parser.parse_args()
    
    if args.command == 'serve':
        return serve_command(args)
    elif args.command == 'file':
        return asyncio.run(file_command(args))
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
