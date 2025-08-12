/* alert_activity.js – v2
 * --------------------------------------------------------------
 * Loads /alerts/alert JSON and populates the table.
 * Adds extra logging and a friendly “no alerts” message.
 * -------------------------------------------------------------- */
'use strict';

const API_ALERTS = '/alerts/alert';             // adjust if your blueprint path differs
let autoRefresh = false;
let timerId;

/* ===== Helpers ===== */
function tsToLocal(ts) {
  if (!ts) return '';
  return /^\d+$/.test(ts)
    ? new Date(Number(ts) * 1000).toLocaleString()
    : new Date(ts).toLocaleString();
}

function log(...args) {
  // quick toggle here if you want to silence debug logs
  console.debug('[alert_activity]', ...args);
}

/* ===== Fetch + render ===== */
async function fetchAlerts() {
  log('Fetching', API_ALERTS);
  const resp = await fetch(API_ALERTS, { cache: 'no-store' });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

function renderTable(rows) {
  const tbody = document.querySelector('#alertTable tbody');
  if (!tbody) {
    console.error('Cannot find <tbody> (#alertTable)')
    return;
  }

  if (rows.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="7" style="text-align:center;padding:1rem;">No alerts yet</td></tr>';
    return;
  }

  const html = rows.map(a => `
      <tr>
        <td>${a.alert_id}</td>
        <td>${tsToLocal(a.ts)}</td>
        <td>${a.alert_type}</td>
        <td>${a.src_ip}</td>
        <td>${a.dst_ip}</td>
        <td>${a.model_name ?? ''}</td>
        <td>${a.details ?? ''}</td>
      </tr>`).join('');

  tbody.innerHTML = html;
}

async function loadAlerts() {
  try {
    const rows = await fetchAlerts();
    renderTable(rows);
  } catch (err) {
    console.error('Failed to load alerts:', err);
  }
}

/* ===== Auto-refresh ===== */
function toggleAuto() {
  autoRefresh = !autoRefresh;
  document.getElementById('autoState').textContent = autoRefresh ? 'On' : 'Off';
  if (autoRefresh) {
    loadAlerts();
    timerId = setInterval(loadAlerts, 15_000);   // 15 s
  } else {
    clearInterval(timerId);
  }
}

/* ===== Boot ===== */
function boot() {
  loadAlerts();                                 // initial fill
  // wire buttons in case inline onclick attr was removed
  document.querySelector('.refresh')?.addEventListener('click', loadAlerts);
  document.querySelector('.auto')?.addEventListener('click', toggleAuto);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  // script loaded after DOM – safe to run immediately
  boot();
}
