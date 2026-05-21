/**
 * Farmer Pro - API Services
 */
import { CONFIG } from './state.js';

export const ApiService = {
    async getDevices() {
        const response = await fetch(`${CONFIG.API_BASE}/devices`);
        if (!response.ok) throw new Error('Failed to fetch devices');
        return response.json();
    },

    async startWorker(serial, index) {
        const response = await fetch(`${CONFIG.API_BASE}/worker/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_serial: serial, ld_index: index })
        });
        return response.json();
    },

    async stopWorker(serial) {
        const response = await fetch(`${CONFIG.API_BASE}/worker/stop/${serial}`, {
            method: 'POST'
        });
        return response.json();
    },

    async getConfig(index) {
        const response = await fetch(`${CONFIG.API_BASE}/config/${index}`);
        return response.json();
    },

    async saveConfig(index, config) {
        const response = await fetch(`${CONFIG.API_BASE}/config/${index}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return response.ok;
    },

    async getFruits() {
        const response = await fetch(`${CONFIG.API_BASE}/fruits`);
        return response.json();
    }
};
