/*
 * Remi — AI Pharmacy Agent
 *
 * @file main.js
 * @description Electron main process. Creates the native window Remi runs
 *              in, builds the application menu (with keyboard shortcuts
 *              that the renderer can't intercept itself, e.g. Cmd/Ctrl+N),
 *              persists window size/position between launches, and bridges
 *              menu actions + window controls to the renderer via IPC.
 *
 *              index.html is loaded as-is and remains fully capable of
 *              running standalone in a plain browser (see preload.js) —
 *              this file only ADDS native chrome on top of it, it never
 *              requires it.
 *
 * @author Anam
 */

const { app, BrowserWindow, Menu, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// ── WINDOW STATE PERSISTENCE ──────────────────────────────────
// Plain JSON file in Electron's per-user data directory rather than a
// dependency like electron-store — window state is two numbers and a
// position, which doesn't justify pulling in a package for it.
const WINDOW_STATE_PATH = path.join(app.getPath('userData'), 'window-state.json');
const DEFAULT_WINDOW_STATE = { width: 1440, height: 900, x: undefined, y: undefined };

/**
 * Reads the last-saved window bounds from disk.
 * Falls back to DEFAULT_WINDOW_STATE on first launch or if the file is
 * missing/corrupted — a malformed state file should never prevent the
 * app from opening.
 * @returns {{width:number, height:number, x?:number, y?:number}}
 */
function loadWindowState(){
  try{
    const raw = fs.readFileSync(WINDOW_STATE_PATH, 'utf8');
    const parsed = JSON.parse(raw);
    console.log('[Remi/main] Loaded window state:', parsed);
    return { ...DEFAULT_WINDOW_STATE, ...parsed };
  } catch(err){
    console.log('[Remi/main] No saved window state, using defaults.');
    return { ...DEFAULT_WINDOW_STATE };
  }
}

/**
 * Writes the given window bounds to disk so the next launch can restore
 * them. Called on 'resize'/'move' (debounced via 'close', see below) —
 * we only persist on close rather than on every resize event to avoid
 * hammering disk I/O while the user is actively dragging the window.
 * @param {BrowserWindow} win
 */
function saveWindowState(win){
  if(win.isDestroyed()) return;
  const bounds = win.getBounds();
  try{
    fs.writeFileSync(WINDOW_STATE_PATH, JSON.stringify(bounds));
    console.log('[Remi/main] Saved window state:', bounds);
  } catch(err){
    console.log('[Remi/main] Failed to save window state:', err.message);
  }
}

let mainWindow = null;

/**
 * Creates and configures the main application window.
 *
 * Titlebar strategy differs by platform because Electron's "give me a
 * native-feeling custom titlebar" support differs by platform:
 *   - macOS: `titleBarStyle: 'hiddenInset'` keeps the real native traffic
 *     lights (so they behave exactly like every other Mac app) while
 *     hiding the rest of the OS title bar, so our own HTML topbar can
 *     occupy that space. `trafficLightPosition` nudges them to align
 *     with our topbar's vertical center.
 *   - Windows/Linux: there's no native equivalent, so we go fully
 *     frameless (`frame: false`) and the renderer draws its own
 *     minimize/maximize/close buttons, wired up via IPC below.
 *
 * @returns {BrowserWindow} The created window.
 */
function createWindow(){
  const state = loadWindowState();

  mainWindow = new BrowserWindow({
    width: state.width,
    height: state.height,
    x: state.x,
    y: state.y,
    minWidth: 1440,
    minHeight: 900,
    resizable: true,
    backgroundColor: '#080D1A',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    trafficLightPosition: process.platform === 'darwin' ? { x: 16, y: 18 } : undefined,
    frame: process.platform === 'darwin', // hiddenInset still needs a frame; win/linux go frameless below
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if(process.platform !== 'darwin'){
    mainWindow.setMenuBarVisibility(false); // we render our own custom titlebar controls instead
  }

  mainWindow.loadFile('index.html');
  console.log('[Remi/main] Window created with bounds:', state);

  mainWindow.on('resize', () => scheduleSaveWindowState());
  mainWindow.on('move', () => scheduleSaveWindowState());
  mainWindow.on('close', () => saveWindowState(mainWindow));

  return mainWindow;
}

// Debounce frequent resize/move events into a single deferred save so
// dragging a window doesn't write to disk dozens of times per second.
let saveStateTimer = null;
function scheduleSaveWindowState(){
  if(saveStateTimer) clearTimeout(saveStateTimer);
  saveStateTimer = setTimeout(() => saveWindowState(mainWindow), 400);
}

// ── APPLICATION MENU ───────────────────────────────────────────
// Menu accelerators exist specifically because the renderer CANNOT
// reliably intercept combos like Cmd/Ctrl+N or Cmd/Ctrl+P itself — those
// are reserved by browsers/OS at a level below JS keydown listeners.
// Routing them through native menu items and forwarding via IPC is the
// only robust way to support them in a desktop app.

/**
 * Sends a named action to the renderer over the 'menu:action' channel.
 * Centralized here so every menu item's click handler is a one-liner.
 * @param {string} action - Action identifier the renderer's listener switches on.
 */
function sendMenuAction(action){
  console.log('[Remi/main] Menu action:', action);
  if(mainWindow && !mainWindow.isDestroyed()){
    mainWindow.webContents.send('menu:action', action);
  }
}

/**
 * Builds and applies the native application menu (File / View / Help).
 * Must run after `app.whenReady()` since Menu.setApplicationMenu needs
 * an initialized app.
 */
function buildAppMenu(){
  const isMac = process.platform === 'darwin';

  const template = [
    ...(isMac ? [{
      label: 'Remi',
      submenu: [
        { label: 'About Remi', click: () => showAboutDialog() },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),
    {
      label: 'File',
      submenu: [
        { label: 'New Shift', accelerator: 'CmdOrCtrl+N', click: () => sendMenuAction('new-shift') },
        { label: 'End Shift', click: () => sendMenuAction('end-shift') },
        { type: 'separator' },
        { label: 'Export Shift Report', accelerator: 'CmdOrCtrl+R', click: () => sendMenuAction('export-report') },
        { type: 'separator' },
        { label: 'Settings…', accelerator: 'CmdOrCtrl+,', click: () => sendMenuAction('settings') },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit', label: 'Quit' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { label: 'Tech Mode', accelerator: 'CmdOrCtrl+T', click: () => sendMenuAction('view-tech') },
        { label: 'Patient Mode', accelerator: 'CmdOrCtrl+P', click: () => sendMenuAction('view-patient') },
        { type: 'separator' },
        { label: 'Toggle Sidebar', accelerator: 'CmdOrCtrl+B', click: () => sendMenuAction('toggle-sidebar') },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'toggleDevTools' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        { label: 'Documentation', click: () => shell.openPath(path.join(__dirname, 'docs', 'ARCHITECTURE.md')) },
        { label: 'About Remi', click: () => showAboutDialog() }
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

/** Shows a simple About dialog — used in the Help menu and (on mac) the app menu, since app.showAboutPanel() styling varies a lot by platform and a dialog box is more predictable here. */
function showAboutDialog(){
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'About Remi',
    message: 'Remi — AI Pharmacy Agent',
    detail: 'Agentic AI assistant for the retail pharmacy counter.\nVersion 1.0.0\nBuilt by Anam.',
    buttons: ['OK']
  });
}

// ── IPC: RENDERER → MAIN ───────────────────────────────────────
// Minimal surface, mirroring the minimal contextBridge surface in
// preload.js — every channel here corresponds to exactly one exposed
// renderer-facing function, nothing more.

ipcMain.on('window:set-title', (event, title) => {
  if(mainWindow && !mainWindow.isDestroyed()) mainWindow.setTitle(title);
});
ipcMain.on('window:minimize', () => mainWindow && mainWindow.minimize());
ipcMain.on('window:maximize', () => {
  if(!mainWindow) return;
  if(mainWindow.isMaximized()) mainWindow.unmaximize(); else mainWindow.maximize();
});
ipcMain.on('window:close', () => mainWindow && mainWindow.close());

// ── APP LIFECYCLE ──────────────────────────────────────────────

app.whenReady().then(() => {
  console.log('[Remi/main] App ready, creating window.');
  buildAppMenu();
  createWindow();

  app.on('activate', () => {
    // macOS convention: re-create a window if the user clicks the dock
    // icon after closing every window without quitting the app.
    if(BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  // Windows/Linux convention: quit when the last window closes.
  // macOS apps conventionally stay running in the dock until Cmd+Q.
  if(process.platform !== 'darwin') app.quit();
});
