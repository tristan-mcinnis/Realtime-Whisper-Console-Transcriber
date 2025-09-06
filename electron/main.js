const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

let mainWindow;
let child = null;

function resolvePython() {
  // Try python3, then python, then py -3 (Windows)
  const candidates = [
    { cmd: 'python3', args: ['--version'] },
    { cmd: 'python', args: ['--version'] },
    { cmd: 'py', args: ['-3', '--version'] },
  ];
  for (const c of candidates) {
    try {
      const res = spawnSync(c.cmd, c.args, { stdio: 'ignore' });
      if (res.status === 0) {
        if (c.cmd === 'py') return { cmd: 'py', prefix: ['-3'] };
        return { cmd: c.cmd, prefix: [] };
      }
    } catch {}
  }
  return null;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 980,
    height: 640,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    title: 'Console Transcriber',
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

function startProcess(args) {
  if (child) {
    mainWindow.webContents.send('process-data', '\n[Already running]\n');
    return;
  }
  const py = resolvePython();
  if (!py) {
    mainWindow.webContents.send('process-data', 'Python not found. Install Python 3 and ensure it is in PATH.');
    return;
  }
  const repoRoot = path.join(__dirname, '..');
  const script = path.join(repoRoot, 'transcribe.py');
  const fullArgs = [...py.prefix, script, ...args];
  child = spawn(py.cmd, fullArgs, { cwd: repoRoot, shell: false, windowsHide: true });

  child.stdout.on('data', (d) => {
    mainWindow.webContents.send('process-data', d.toString());
  });
  child.stderr.on('data', (d) => {
    mainWindow.webContents.send('process-data', d.toString());
  });
  child.on('close', (code) => {
    mainWindow.webContents.send('process-exited', code);
    child = null;
  });
}

ipcMain.handle('pick-file', async () => {
  const res = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Audio', extensions: ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'oga', 'aac', 'wma'] },
      { name: 'All', extensions: ['*'] }
    ]
  });
  if (res.canceled || !res.filePaths[0]) return null;
  return res.filePaths[0];
});

ipcMain.handle('start-live', async (_evt, opts) => {
  const args = ['live'];
  if (opts.engine) args.push('--engine', opts.engine);
  if (typeof opts.language === 'string') args.push('--language', opts.language);
  if (typeof opts.model === 'string') args.push('--model', opts.model);
  if (opts.engine === 'legacy') {
    if (opts.bufferSize) args.push('--buffer-size', String(opts.bufferSize));
    if (opts.phraseTimeLimit) args.push('--phrase-time-limit', String(opts.phraseTimeLimit));
  }
  if (opts.plain) args.push('--plain');
  if (opts.noSave) args.push('--no-save');
  startProcess(args);
});

ipcMain.handle('stop', async () => {
  if (child) {
    try { child.kill(); } catch {}
  }
});

ipcMain.handle('run-diarize', async (_evt, opts) => {
  const args = ['diarize', opts.path];
  if (opts.device) args.push('--device', opts.device);
  if (opts.jsonOut) args.push('--json-out', opts.jsonOut);
  startProcess(args);
});
