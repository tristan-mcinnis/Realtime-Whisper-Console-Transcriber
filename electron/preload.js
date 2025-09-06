const { contextBridge, ipcRenderer } = require('electron');

/**
 * Expose a minimal, focused API for the renderer:
 *  • startServer / stopServer – spawn / terminate whisperlivekit-server
 *  • getWsUrl(port)          – convenience helper to build ws url
 *  • onServerLog(cb)         – streaming stdout / stderr from server
 */
contextBridge.exposeInMainWorld('api', {
  startServer: (opts = {}) => ipcRenderer.invoke('start-server', opts),
  stopServer: () => ipcRenderer.invoke('stop-server'),
  getWsUrl:  (port = 8801) => ipcRenderer.invoke('get-ws-url', port),

  // listener for streaming logs from the backend
  onServerLog: (cb) =>
    ipcRenderer.on('server-log', (_e, data) => { if (cb) cb(data); }),
});
