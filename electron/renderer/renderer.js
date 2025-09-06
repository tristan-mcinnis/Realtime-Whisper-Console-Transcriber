(function() {
  const $ = (sel) => document.querySelector(sel);
  const output = $('#output');
  const diarOut = $('#diarOut');
  // track which subprocess is currently active ('live' | 'diarize')
  let current = null;

  function append(el, text) {
    el.textContent += text;
    el.scrollTop = el.scrollHeight;
  }

  // Tabs
  document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
  });

  // Engine toggle -> show legacy options
  const engine = $('#engine');
  const legacyOpts = $('#legacy-opts');
  engine.addEventListener('change', () => {
    legacyOpts.style.display = engine.value === 'legacy' ? '' : 'none';
  });

  // Live controls
  $('#start').addEventListener('click', async () => {
    output.textContent += '\n[Starting...]\n';
    current = 'live';
    window.api.startLive({
      engine: engine.value,
      language: $('#language').value,
      model: $('#model').value,
      bufferSize: Number($('#bufferSize').value),
      phraseTimeLimit: Number($('#phraseTimeLimit').value),
      plain: $('#plain').checked,
      noSave: $('#noSave').checked,
    });
  });

  $('#stop').addEventListener('click', async () => {
    await window.api.stop();
  });

  $('#clear').addEventListener('click', () => { output.textContent = ''; });
  $('#copy').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(output.textContent);
    } catch {
      // ignore
    }
  });

  // Diarize controls
  $('#browse').addEventListener('click', async () => {
    const p = await window.api.pickFile();
    if (p) $('#filePath').value = p;
  });
  $('#runDiarize').addEventListener('click', async () => {
    diarOut.textContent += '\n[Running diarize...]\n';
    const path = $('#filePath').value.trim();
    if (!path) return;
    current = 'diarize';
    window.api.runDiarize({
      path,
      device: $('#device').value,
    });
  });

  // Streamed data and exit events
  window.api.onData((data) => {
    if (current === 'diarize') append(diarOut, data);
    else append(output, data); // default to live
  });
  window.api.onExit((code) => {
    const msg = `\n[Process exited with code ${code}]\n`;
    if (current === 'diarize') append(diarOut, msg);
    else append(output, msg);
    current = null;
  });
})();
