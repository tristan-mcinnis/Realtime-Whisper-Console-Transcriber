# Whisper Console Transcriber

A real-time speech-to-text transcriber using the Whisper model, designed for efficiency and ease of use in the console. This tool leverages the faster_whisper library and Rich to provide a seamless user experience for transcribing audio inputs on the fly.

## Background

Whisper is a state-of-the-art model for automatic speech recognition (ASR). This project utilizes the Whisper model and provides a practical interface for capturing live audio input, transcribing it, and displaying the results in real time. It's designed to be flexible, allowing the user to choose the language of transcription and offering a buffer system to handle continuous speech.

## Features

-  Real-time speech-to-text using Whisper model
-  Support for multiple languages
-  Console-based application with rich text formatting
-  Automatic ambient noise adjustment
-  Saves transcriptions to a file in the Downloads folder

## Installation

To install and run this project, follow these steps:

1. **Clone the repo:**
    ```sh
    git clone https://github.com/nexuslux/Realtime-Whisper-Console-Transcriber
    cd WhisperConsoleTranscriber
    ```

2. **Set up a virtual environment (optional but recommended):**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install required dependencies:**
    ```sh
    pip install faster_whisper speechrecognition rich
    ```

## How to Run

1. **Run the script:**
    ```sh
    python script_name.py
    ```

2. **Follow the prompts:**
    - After running the script, you will be prompted to enter the language code (e.g., 'en' for English, 'zh' for Chinese, 'es' for Spanish).
    - The application will then adjust for ambient noise and start capturing audio.

3. **Start speaking or playing audio:**
    - Once you start speaking, the application will transcribe your speech in real time.
    - Transcriptions are buffered and displayed in chunks.

4. **Stop listening:**
    - Press `CTRL + C` to stop the transcription process.
    - The transcriptions will automatically be saved to a text file in your Downloads folder.

## Example

```sh
python transcribe.py
 ```

After this you will be asked to enter the main language.
	•	Enter the language code: en
	•	Start speaking. The application will display transcribed text in the console.
	•	End the session with CTRL + C. The output will be saved to a text file in the Downloads folder.
Customization
You can customize the following parameters in the script:
	•	buffer_size: Number of segments to buffer before displaying the transcription.
	•	language_code: Set your preferred default language code for transcription.
