/**
 * Farmer Pro - Main Application Logic
 */
import { state, elements, CONFIG } from './state.js';
import { ApiService } from './api.js';
import { log, updateServerStatus, updateStats, escapeHtml } from './utils.js';

// ==================== Actions ====================
async function refreshDevices() {
    try {
        state.devices = await ApiService.getDevices();
        state.stats.devices = state.devices.length;
        state.stats.running = state.devices.filter(d => d.status === 'running').length;

        renderDeviceList();
        updateStats();
        log(`Found ${state.devices.length} device(s)`, 'success');
    } catch (error) {
        log(`Error fetching devices: ${error.message}`, 'error');
    }
}

async function handleStartStop(device, action) {
    try {
        const result = action === 'start'
            ? await ApiService.startWorker(device.serial, device.index)
            : await ApiService.stopWorker(device.serial);

        if (result.status === 'ok') {
            log(`${action === 'start' ? 'Started' : 'Stopped'} worker for ${device.name}`, action === 'start' ? 'success' : 'warning');
            device.status = action === 'start' ? 'running' : 'idle';
            renderDeviceList();
            updateStats();
        } else {
            log(`Failed to ${action} worker: ${result.message}`, 'error');
        }
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
    }
}

// ==================== Modal Logic ====================
async function openConfigModal(device) {
    state.selectedDevice = device;
    try {
        const config = await ApiService.getConfig(device.index);
        const allFruits = await ApiService.getFruits();

        elements.cfgBuyFruits.checked = config.enable_buy_fruits ?? true;
        elements.cfgBuyVoi.checked = config.enable_buy_voi ?? true;
        elements.cfgHarvestSell.checked = config.enable_harvest_sell ?? true;
        elements.cfgTimeGate.checked = config.use_time_gate ?? true;
        elements.cfgFirstRun.checked = config.first_run_immediate ?? true;
        elements.cfgThreshold.value = config.threshold ?? 0.95;
        elements.cfgThresholdValue.textContent = parseFloat(elements.cfgThreshold.value).toFixed(2);
        elements.cfgHarvestCycles.value = config.harvest_sell_cycles ?? 1;
        elements.cfgSellCycles.value = config.sell_cycles_after_harvest ?? 1;

        const selectedFruits = config.fruits || {};
        elements.fruitList.innerHTML = Object.keys(allFruits).map(name => `
      <label class="toggle-row" style="padding: 8px 12px;">
        <span style="font-size: 0.8rem">${name}</span>
        <div class="switch">
            <input type="checkbox" class="fruit-checkbox" data-fruit="${name}" ${selectedFruits[name]?.buy !== false ? 'checked' : ''}>
            <span class="slider"></span>
        </div>
      </label>
    `).join('');

        elements.configModal.classList.add('open');
    } catch (error) {
        log(`Error loading settings: ${error.message}`, 'error');
    }
}

async function handleSaveConfig() {
    if (!state.selectedDevice) return;

    const fruitChecks = document.querySelectorAll('.fruit-checkbox');
    const fruits = {};
    fruitChecks.forEach(cb => { fruits[cb.dataset.fruit] = { buy: cb.checked }; });

    const config = {
        enable_buy_fruits: elements.cfgBuyFruits.checked,
        enable_buy_voi: elements.cfgBuyVoi.checked,
        enable_harvest_sell: elements.cfgHarvestSell.checked,
        use_time_gate: elements.cfgTimeGate.checked,
        first_run_immediate: elements.cfgFirstRun.checked,
        threshold: parseFloat(elements.cfgThreshold.value),
        harvest_sell_cycles: parseInt(elements.cfgHarvestCycles.value) || 1,
        sell_cycles_after_harvest: parseInt(elements.cfgSellCycles.value) || 1,
        fruits: fruits
    };

    const success = await ApiService.saveConfig(state.selectedDevice.index, config);
    if (success) {
        log(`Configuration saved for ${state.selectedDevice.name}`, 'success');
        elements.configModal.classList.remove('open');
    }
}

// ==================== WebSocket ====================
function initWebSocket() {
    if (state.ws?.readyState === WebSocket.OPEN) return;

    state.ws = new WebSocket(CONFIG.WS_URL);

    state.ws.onopen = () => {
        state.wsConnected = true;
        updateServerStatus(true);
        log('Connected to backend', 'success');
    };

    state.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'log') log(`[${data.device_serial}] ${data.message}`);
        else if (data.type === 'worker_started' || data.type === 'worker_stopped') refreshDevices();
    };

    state.ws.onclose = () => {
        state.wsConnected = false;
        updateServerStatus(false);
        setTimeout(initWebSocket, 3000);
    };
}

// ==================== Navigation ====================
function switchView(viewId) {
    const targetId = `view${viewId.charAt(0).toUpperCase() + viewId.slice(1)}`;

    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewId);
    });

    elements.views.forEach(view => {
        view.classList.toggle('active', view.id === targetId);
    });

    log(`Switched to ${viewId} view`);
}

// ==================== Toast Logic ====================
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Icons
    let iconSvg = '';
    if (type === 'success') iconSvg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
    else if (type === 'error') iconSvg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
    else if (type === 'warning') iconSvg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
    else iconSvg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';

    toast.innerHTML = `
        <div class="toast-icon">${iconSvg}</div>
        <div class="toast-content">
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;

    // Interaction to dismiss early
    toast.onclick = () => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    };

    if (elements.toastContainer) {
        elements.toastContainer.appendChild(toast);
        // Clean up after animation + consistent delay (3s visual + 0.3s fade out)
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('hide');
                setTimeout(() => { if (toast.parentElement) toast.remove(); }, 300);
            }
        }, 3000);
    }
}

// ==================== Update Logic ====================
async function checkForUpdate(showNoUpdate = false) {
    try {
        if (!window.__TAURI__?.updater) {
            if (showNoUpdate) showToast('Updater plugin not loaded', 'error');
            return;
        }

        log('Checking for updates...');
        // Mock Update for Testing
        // const update = { version: '2.0.0', body: '- Added awesome features\n- Fixed bugs', downloadAndInstall: async () => { } };
        const update = await window.__TAURI__.updater.check();

        if (update) {
            log(`New version found: ${update.version}`, 'success');
            // Reset Modal State
            elements.updateInfo.style.display = 'flex';
            elements.updateActions.style.display = 'flex';
            elements.updateProgress.classList.add('hidden');
            elements.updateProgress.style.display = 'none'; // Ensure hidden

            elements.updateModal.classList.add('open');

            // Handle Confirm
            elements.btnConfirmUpdate.onclick = async () => {
                // Switch to Progress View
                elements.updateInfo.style.display = 'none';
                elements.updateActions.style.display = 'none';
                elements.updateProgress.classList.remove('hidden');
                elements.updateProgress.style.display = 'flex';

                log('Downloading update...', 'success');

                try {
                    await update.downloadAndInstall((event) => {
                        switch (event.event) {
                            case 'Started':
                                elements.progressText.textContent = `Started downloading...`;
                                elements.progressBarFill.style.width = `0%`;
                                break;
                            case 'Progress':
                                elements.progressText.textContent = `Downloading...`;
                                // Simplistic visual progress if needed, usually we rely on "Downloading..." text
                                break;
                            case 'Finished':
                                elements.progressText.textContent = `Download complete. Installing...`;
                                elements.progressBarFill.style.width = `100%`;
                                break;
                        }
                    });

                    log('Update installed, restarting...', 'success');
                    showToast('Update installed successfully! Restarting...', 'success');
                } catch (e) {
                    log(`Update failed: ${e}`, 'error');
                    elements.progressText.textContent = "Update Failed!";
                    elements.progressText.style.color = "var(--color-error)";
                    showToast(`Update failed: ${e}`, 'error');
                    setTimeout(() => {
                        elements.updateModal.classList.remove('open');
                    }, 3000);
                }
            };

            // Handle Cancel
            elements.btnCancelUpdate.onclick = () => {
                elements.updateModal.classList.remove('open');
            };
        } else if (showNoUpdate) {
            log('You are currently on the latest version', 'success');
            showToast('Your software is up to date!', 'success');
        }
    } catch (err) {
        log(`Update check failed: ${err}`, 'error');
        if (showNoUpdate) showToast(`Update check failed: ${err}`, 'error');
    }
}

// ==================== Rendering ====================
function renderDeviceList() {
    elements.deviceCount.textContent = `${state.devices.length} ACTIVE`;
    elements.deviceList.innerHTML = state.devices.map((device, index) => `
    <div class="device-row ${device.status === 'running' ? 'active' : ''}">
      <div style="width: 50px" class="font-mono opacity-40">${index + 1}</div>
      
      <div style="flex: 2" class="flex items-center gap-md">
        <div class="glass-card" style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.05)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>
        </div>
        <div class="device-name">${escapeHtml(device.name)}</div>
      </div>

      <div style="flex: 1.5" class="device-serial opacity-50">${device.serial}</div>

      <div style="flex: 1">
        <span class="status-badge ${device.status}">${device.status === 'running' ? 'Running' : 'Idle'}</span>
      </div>

      <div style="width: 100px; text-align: left" class="flex justify-start gap-sm">
          <button class="btn ${device.status === 'running' ? 'btn-stop' : 'btn-primary'} btn-icon" 
              data-action="${device.status === 'running' ? 'stop' : 'start'}"
              data-serial="${device.serial}"
              style="width: 32px; height: 32px">
              ${device.status === 'running'
            ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12"></rect></svg>'
            : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>'}
          </button>

          <button class="btn btn-ghost btn-icon" data-action="config" data-serial="${device.serial}" style="width: 32px; height: 32px">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          </button>
      </div>
    </div>
    `).join('');

    elements.deviceList.querySelectorAll('[data-action]').forEach(btn => {
        btn.onclick = () => {
            const device = state.devices.find(d => d.serial === btn.dataset.serial);
            if (btn.dataset.action === 'config') openConfigModal(device);
            else handleStartStop(device, btn.dataset.action);
        };
    });
}

// ==================== Init ====================
function init() {
    document.documentElement.setAttribute('data-theme', state.theme);
    elements.settingDarkMode.checked = state.theme === 'dark';

    // Sidebar Collapse
    if (state.sidebarMini) elements.sidebar.classList.add('mini');
    elements.btnCollapseSidebar.onclick = () => {
        state.sidebarMini = !state.sidebarMini;
        elements.sidebar.classList.toggle('mini', state.sidebarMini);
        localStorage.setItem('sidebarMini', state.sidebarMini);
    };

    // Navigation
    elements.navItems.forEach(item => {
        item.onclick = () => switchView(item.dataset.view);
    });

    elements.btnRefresh.onclick = refreshDevices;
    elements.btnTheme.onclick = toggleTheme;
    elements.settingDarkMode.onchange = toggleTheme;

    function toggleTheme() {
        state.theme = state.theme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', state.theme);
        localStorage.setItem('theme', state.theme);
        elements.settingDarkMode.checked = state.theme === 'dark';
    }

    elements.btnClearLogs.onclick = () => { elements.logContent.innerHTML = ''; log('Logs cleared'); };
    elements.btnScrollLock.onclick = () => {
        state.autoScroll = !state.autoScroll;
        elements.btnScrollLock.classList.toggle('active', state.autoScroll);
    };

    elements.btnCloseModal.onclick = () => elements.configModal.classList.remove('open');
    elements.btnSaveConfig.onclick = handleSaveConfig;
    elements.cfgThreshold.oninput = (e) => elements.cfgThresholdValue.textContent = parseFloat(e.target.value).toFixed(2);

    elements.btnCheckUpdate.onclick = () => checkForUpdate(true);

    initWebSocket();
    setTimeout(refreshDevices, 1000);
    setTimeout(() => checkForUpdate(false), 2000);
}

document.addEventListener('DOMContentLoaded', init);
