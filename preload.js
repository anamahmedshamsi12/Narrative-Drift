/*
 * Remi — AI Pharmacy Agent
 *
 * @file preload.js
 * @description Secure context bridge between the Electron main process
 *              and the renderer (index.html). Runs in an isolated context
 *              with access to Node APIs, and exposes only a small,
 *              named surface — `window.remiAPI` — to the renderer's
 *              actual JS. The renderer never gets `require`, `process`,
 *              or any other raw Node/Electron primitive.
 *
 *              The renderer always feature-detects `window.remiAPI`
 *              before using it (`if (window.remiAPI) {...}`), since the
 *              same index.html also has to run standalone in a plain
 *              browser with no Electron underneath it at all.
 *
 * @author Anam
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('remiAPI', {
  /** True whenever the renderer is running inside Electron — lets index.html decide whether to show native-window-only UI (custom titlebar controls, etc.). */
  isElectron: true,

  /** 'darwin' | 'win32' | 'linux' — used to decide whether to render custom minimize/maximize/close buttons (only needed off-macOS; see main.js's titlebar strategy). */
  platform: process.platform,

  /**
   * Updates the native window title.
   * @param {string} title - Full title string, e.g. "Remi — Main Street Pharmacy — 10:42 AM".
   */
  setTitle(title){ ipcRenderer.send('window:set-title', title); },

  /** Minimizes the window. Only used by the custom titlebar controls on Windows/Linux. */
  minimizeWindow(){ ipcRenderer.send('window:minimize'); },

  /** Toggles maximize/restore. Only used by the custom titlebar controls on Windows/Linux. */
  maximizeWindow(){ ipcRenderer.send('window:maximize'); },

  /** Closes the window. Only used by the custom titlebar controls on Windows/Linux. */
  closeWindow(){ ipcRenderer.send('window:close'); },

  /**
   * Subscribes to menu actions forwarded from the native application
   * menu (File/View/Help) in main.js — these exist because the
   * renderer can't intercept accelerators like Cmd/Ctrl+N itself.
   * @param {(action:string)=>void} callback - Called with an action id: 'new-shift' | 'end-shift' | 'export-report' | 'view-tech' | 'view-patient' | 'toggle-sidebar' | 'settings'.
   */
  onMenuAction(callback){
    ipcRenderer.on('menu:action', (event, action) => callback(action));
  }
});

console.log('[Remi/preload] remiAPI exposed to renderer.');
