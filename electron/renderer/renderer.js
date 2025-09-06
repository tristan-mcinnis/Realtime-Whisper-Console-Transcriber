(function() {
  const $ = (sel) => document.querySelector(sel);
  const output = $('#output');
  
  // Server and connection state
  let websocket = null;
  let mediaRecorder = null;
  let mediaStream = null;
  const PORT = 8801;
  
  // Append text to output with auto-scroll
  function append(text) {
    output.textContent += text;
    output.scrollTop = output.scrollHeight;
  }
  
  // Format and display JSON response from server
  function handleServerMessage(data) {
    try {
      const response = JSON.parse(data);
      
      // Check if server is ready to stop
      if (response.type === 'ready_to_stop') {
        append('\n[Processing complete]\n');
        return;
      }
      
      // Handle lines with speaker diarization
      if (response.lines && Array.isArray(response.lines)) {
        for (const line of response.lines) {
          const speaker = line.speaker || line.spk || '';
          const text = line.text || line.line || '';
          
          if (speaker && text) {
            append(`\n[${speaker}] ${text}`);
          } else if (text) {
            append(`\n${text}`);
          }
        }
      } 
      // Handle buffer transcription/diarization if present
      else if (response.buffer_transcription || response.buffer_diarization) {
        // Don't append these to avoid cluttering the output
        // Could display in a separate "live buffer" element if desired
      }
      // For any other format, just show the raw JSON
      else {
        append('\n' + JSON.stringify(response, null, 2));
      }
    } catch (e) {
      // If not valid JSON, just append as text
      append(data);
    }
  }
  
  // Connect to WebSocket server and set up handlers
  function connectWebSocket() {
    return new Promise((resolve, reject) => {
      window.api.getWsUrl(PORT).then(url => {
        websocket = new WebSocket(url);
        
        websocket.onopen = () => {
          append('\n[WebSocket connected]\n');
          resolve(websocket);
        };
        
        websocket.onmessage = (event) => {
          handleServerMessage(event.data);
        };
        
        websocket.onerror = (error) => {
          append(`\n[WebSocket error: ${error}]\n`);
        };
        
        websocket.onclose = () => {
          append('\n[WebSocket disconnected]\n');
          websocket = null;
        };
      }).catch(reject);
    });
  }
  
  // Start recording from microphone and send to WebSocket
  function startRecording() {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      append('\n[Error: WebSocket not connected]\n');
      return Promise.reject(new Error('WebSocket not connected'));
    }
    
    return navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(stream => {
        mediaStream = stream;
        
        // Use 16kHz audio if possible for better transcription
        const options = { 
          mimeType: 'audio/webm',
          audioBitsPerSecond: 128000
        };
        
        mediaRecorder = new MediaRecorder(stream, options);
        
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0 && websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(event.data);
          }
        };
        
        mediaRecorder.onstop = () => {
          // Send empty blob to signal end of audio stream
          if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(new Blob([]));
          }
        };
        
        // Start recording with small timeslices for low latency
        mediaRecorder.start(250);
        append('\n[Recording started]\n');
        return mediaRecorder;
      });
  }
  
  // Stop recording and clean up
  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      append('\n[Recording stopped]\n');
    }
    
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      mediaStream = null;
    }
    
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.close();
    }
  }
  
  // Start button: start server, connect WebSocket, start recording
  $('#start').addEventListener('click', async () => {
    try {
      // Get options from UI
      const options = {
        port: PORT,
        model: $('#model').value,
        language: $('#language').value,
        diarization: $('#diarization').checked
      };
      
      // Clear previous output
      output.textContent = '';
      append('[Starting server...]\n');
      
      // Start server
      await window.api.startServer(options);
      
      // Wait a moment for server to initialize
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Connect WebSocket
      await connectWebSocket();
      
      // Start recording
      await startRecording();
      
    } catch (error) {
      append(`\n[Error: ${error.message}]\n`);
    }
  });
  
  // Stop button: stop recording, close WebSocket, stop server
  $('#stop').addEventListener('click', async () => {
    stopRecording();
    await window.api.stopServer();
  });
  
  // Clear button: clear output
  $('#clear').addEventListener('click', () => { 
    output.textContent = ''; 
  });
  
  // Copy button: copy output to clipboard
  $('#copy').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(output.textContent);
      append('\n[Copied to clipboard]\n');
    } catch (error) {
      append('\n[Failed to copy to clipboard]\n');
    }
  });
  
  // Listen for server logs
  window.api.onServerLog((data) => {
    append(data);
  });
})();
