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

/**
 * Attempt to build the spawn command/args for whisperlivekit-server.
 * Returns {cmd, args} or null when not available.
 */
function resolveWhisperServer(baseArgs = []) {
  // 1. Direct console script
  if (spawnSync('whisperlivekit-server', ['--version'], { stdio: 'ignore' }).status === 0) {
    return { cmd: 'whisperlivekit-server', args: baseArgs };
  }
  // 2. python -m whisperlivekit.basic_server
  const py = resolvePython();
  if (!py) return null;
  return {
    cmd: py.cmd,
    args: [...py.prefix, '-m', 'whisperlivekit.basic_server', ...baseArgs],
  };
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

function startServer(opts) {
  if (child) {
    mainWindow.webContents.send('server-log', '\n[Server already running]\n');
    return;
  }

  const port = opts?.port || 8801;
  const model = opts?.model || 'base';
  const language = opts?.language || 'en';
  const diar = !!opts?.diarization;

  const baseArgs = ['--host', '127.0.0.1', '--port', String(port),
                    '--model', model, '--lan', language];
  if (diar) baseArgs.push('--diarization');

  const resolved = resolveWhisperServer(baseArgs);
  if (!resolved) {
    mainWindow.webContents.send('server-log', 'Cannot locate whisperlivekit-server. Install with "pip install whisperlivekit".');
    return;
  }

  child = spawn(resolved.cmd, resolved.args, { shell: false, windowsHide: true });

  child.stdout.on('data', (d) => {
    mainWindow.webContents.send('server-log', d.toString());
  });
  child.stderr.on('data', (d) => {
    mainWindow.webContents.send('server-log', d.toString());
  });
  child.on('close', (code) => {
    mainWindow.webContents.send('server-log', `\n[Server exited with code ${code}]\n`);
    child = null;
  });
}

ipcMain.handle('start-server', async (_evt, opts) => {
  startServer(opts || {});
});

ipcMain.handle('stop-server', async () => {
  if (child) {
    try { child.kill(); } catch {}
  }
});

ipcMain.handle('get-ws-url', async (_evt, port = 8801) => {
  return `ws://127.0.0.1:${port}/asr`;
});
