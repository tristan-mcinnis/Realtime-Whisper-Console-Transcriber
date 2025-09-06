(function() {
  const $ = (sel) => document.querySelector(sel);
  const output = $('#output');
  const diarOut = $('#diarOut');

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
    window.api.runDiarize({
      path,
      device: $('#device').value,
    });
  });

  // Streamed data and exit events
  window.api.onData((data) => {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    if (activeTab === 'live') append(output, data);
    else append(diarOut, data);
  });
  window.api.onExit((code) => {
    const msg = `\n[Process exited with code ${code}]\n`;
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    if (activeTab === 'live') append(output, msg);
    else append(diarOut, msg);
  });
})();
