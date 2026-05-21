/**
 * Farmer Pro - Global State & Constants
 */

export const CONFIG = {
    API_BASE: 'http://127.0.0.1:8765',
    WS_URL: 'ws://127.0.0.1:8765/ws',
};

export const state = {
    devices: [],
    selectedDevice: null,
    ws: null,
    wsConnected: false,
    autoScroll: true,
    sidebarMini: localStorage.getItem('sidebarMini') === 'true',
    theme: localStorage.getItem('theme') || 'dark',
    stats: {
        devices: 0,
        running: 0,
        cycles: 0,
        uptime: 0
    }
};

export const elements = {
    // Header
    serverStatus: document.getElementById('serverStatus'),
    btnRefresh: document.getElementById('btnRefresh'),
    btnTheme: document.getElementById('btnTheme'),

    // Sidebar
    deviceCount: document.getElementById('deviceCount'),
    deviceList: document.getElementById('deviceList'),

    // Navigation
    navItems: document.querySelectorAll('.nav-item'),
    views: document.querySelectorAll('.view-content'),

    // Stats
    statRunning: document.getElementById('statRunning'),
    statCycles: document.getElementById('statCycles'),


    // Logs
    logContent: document.getElementById('logContent'),
    btnClearLogs: document.getElementById('btnClearLogs'),
    btnScrollLock: document.getElementById('btnScrollLock'),

    // Modal
    configModal: document.getElementById('configModal'),
    btnCloseModal: document.getElementById('btnCloseModal'),
    btnCancelConfig: document.getElementById('btnCancelConfig'),
    btnSaveConfig: document.getElementById('btnSaveConfig'),
    fruitList: document.getElementById('fruitList'),

    // Config fields
    cfgBuyFruits: document.getElementById('cfgBuyFruits'),
    cfgBuyVoi: document.getElementById('cfgBuyVoi'),
    cfgHarvestSell: document.getElementById('cfgHarvestSell'),
    cfgTimeGate: document.getElementById('cfgTimeGate'),
    cfgFirstRun: document.getElementById('cfgFirstRun'),
    cfgThreshold: document.getElementById('cfgThreshold'),
    cfgThresholdValue: document.getElementById('cfgThresholdValue'),
    cfgHarvestCycles: document.getElementById('cfgHarvestCycles'),
    cfgSellCycles: document.getElementById('cfgSellCycles'),

    // App Settings View
    settingDarkMode: document.getElementById('settingDarkMode'),

    // Sidebar Collapse
    sidebar: document.getElementById('sidebar'),
    btnCollapseSidebar: document.getElementById('btnCollapseSidebar'),

    // Update
    btnCheckUpdate: document.getElementById('btnCheckUpdate'),
    updateModal: document.getElementById('updateModal'),
    updateVersion: document.getElementById('updateVersion'),
    updateNotes: document.getElementById('updateNotes'),
    btnCancelUpdate: document.getElementById('btnCancelUpdate'),
    btnConfirmUpdate: document.getElementById('btnConfirmUpdate'),
    updateInfo: document.getElementById('updateInfo'),
    updateProgress: document.getElementById('updateProgress'),
    progressBarFill: document.getElementById('progressBarFill'),
    progressText: document.getElementById('progressText'),
    updateActions: document.getElementById('updateActions'),

    // Toast
    toastContainer: document.getElementById('toastContainer'),
    updateActions: document.getElementById('updateActions')
};
