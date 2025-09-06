const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  pickFile: () => ipcRenderer.invoke('pick-file'),
  startLive: (opts) => ipcRenderer.invoke('start-live', opts || {}),
  stop: () => ipcRenderer.invoke('stop'),
  runDiarize: (opts) => ipcRenderer.invoke('run-diarize', opts || {}),
  onData: (cb) => ipcRenderer.on('process-data', (_e, data) => cb && cb(data)),
  onExit: (cb) => ipcRenderer.on('process-exited', (_e, code) => cb && cb(code)),
});
