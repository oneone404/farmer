/**
 * Farmer Pro - Utilities
 */
import { state, elements } from './state.js';

export function formatTime(date = new Date()) {
    return date.toLocaleTimeString('en-US', { hour12: false });
}

export function log(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'opacity-40';
    timeSpan.style.marginRight = '8px';
    timeSpan.style.fontSize = '0.75rem';
    timeSpan.textContent = `[${formatTime()}]`;

    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;

    entry.appendChild(timeSpan);
    entry.appendChild(messageSpan);

    // Clear welcome message if exists
    if (elements.logContent.children.length === 1 && elements.logContent.children[0].classList.contains('opacity-40')) {
        elements.logContent.innerHTML = '';
    }

    elements.logContent.appendChild(entry);

    if (state.autoScroll) {
        elements.logContent.scrollTop = elements.logContent.scrollHeight;
    }
}

export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

export function updateServerStatus(connected) {
    const dot = elements.serverStatus.querySelector('.status-dot');
    const text = elements.serverStatus.querySelector('.status-text');

    if (connected) {
        dot.classList.remove('offline');
        dot.classList.add('online');
        text.textContent = 'CONNECTED';
    } else {
        dot.classList.remove('online');
        dot.classList.add('offline');
        text.textContent = 'DISCONNECTED';
    }
}

export function updateStats() {
    elements.statRunning.textContent = state.stats.running;
    elements.statCycles.textContent = state.stats.cycles;
}

