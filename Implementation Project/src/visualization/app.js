const { createClient } = supabase;
const db = createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);

const CHART_COLORS = ['#5cb85c','#4db6ac','#42a5f5','#ab47bc','#ffa726','#ef5350','#26c6da','#d4e157'];
const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

let chartSpecies  = null;
let chartTimeline = null;
let chartPanel    = null;

let allData      = [];
let filteredData = [];
let activePreset = 'all';
let realtimeSub  = null;
let expandedCard = null;

function initFeed() {
  const img        = document.getElementById('video-feed');
  const connecting = document.getElementById('feed-connecting');
  const offline    = document.getElementById('feed-offline');
  const badge      = document.getElementById('stream-badge');

  badge.textContent = 'Connecting...';
  badge.className   = 'status-badge connecting';
  img.classList.add('hidden');
  connecting.classList.remove('hidden');
  offline.classList.add('hidden');

  img.onload = () => {
    badge.textContent = '● Live';
    badge.className   = 'status-badge live';
    img.classList.remove('hidden');
    connecting.classList.add('hidden');
    offline.classList.add('hidden');
  };

  img.onerror = () => {
    badge.textContent = '○ Offline';
    badge.className   = 'status-badge offline';
    img.classList.add('hidden');
    connecting.classList.add('hidden');
    offline.classList.remove('hidden');
  };

  img.src = CONFIG.PI_STREAM_URL;
}

document.getElementById('feed-expand-btn').addEventListener('click', () => {
  toggleExpand(document.getElementById('feed-panel'));
});

document.querySelectorAll('[data-expand]').forEach(btn => {
  btn.addEventListener('click', () => {
    const card = document.getElementById(btn.dataset.expand);
    toggleExpand(card);
  });
});

function toggleExpand(card) {
  const overlay = document.getElementById('expand-overlay');
  if (expandedCard === card) {
    card.classList.remove('expanded');
    overlay.classList.add('hidden');
    expandedCard = null;
    if (chartSpecies)  chartSpecies.resize();
    if (chartTimeline) chartTimeline.resize();
  } else {
    if (expandedCard) expandedCard.classList.remove('expanded');
    card.classList.add('expanded');
    overlay.classList.remove('hidden');
    expandedCard = card;
    if (chartSpecies)  chartSpecies.resize();
    if (chartTimeline) chartTimeline.resize();
  }
}

document.getElementById('expand-overlay').addEventListener('click', () => {
  if (expandedCard) toggleExpand(expandedCard);
});

async function loadAnalytics() {
  setTableLoading();
  if (!isSupabaseConfigured()) { setAnalyticsError('Add your Supabase credentials to config.js'); return; }

  const { data, error } = await db.from('Detections').select('*').order('created_at');
  if (error || !data) { setAnalyticsError('Could not reach database'); return; }

  allData = data;
  applyFilter(activePreset);
  subscribeRealtime();
}

function applyFilter(preset) {
  activePreset = preset;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.range === preset));

  const now = new Date();
  let cutoff = null;
  if (preset === '7d')    cutoff = new Date(now - 7  * 86400000);
  if (preset === '30d')   cutoff = new Date(now - 30 * 86400000);
  if (preset === 'today') cutoff = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  filteredData = cutoff
    ? allData.filter(d => d.created_at && new Date(d.created_at) >= cutoff)
    : [...allData];

  renderAll(filteredData);
}

function renderAll(data) {
  renderStats(data);
  renderSpeciesChart(data);
  renderTimelineChart(data);
  renderHeatmap(data);
  renderRecentTable(data);
}

function subscribeRealtime() {
  if (realtimeSub) return;
  realtimeSub = db.channel('detections-live')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'Detections' }, payload => {
      const row = payload.new;
      allData.push(row);
      allData.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      applyFilter(activePreset);
      showToast(`New: ${row.species} — ${(row.confidence * 100).toFixed(1)}%`);
    })
    .subscribe();
}

function showToast(msg) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('visible'));
  setTimeout(() => {
    toast.classList.remove('visible');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, 3500);
}

function renderStats(data) {
  const total   = data.length;
  const species = [...new Set(data.map(d => d.species))];
  const avgConf = total > 0 ? data.reduce((s, d) => s + (d.confidence ?? 0), 0) / total : 0;
  const counts  = {};
  data.forEach(d => { counts[d.species] = (counts[d.species] || 0) + 1; });
  const top = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0] ?? '—';

  document.getElementById('stat-total').textContent      = total.toLocaleString();
  document.getElementById('stat-species').textContent    = species.length;
  document.getElementById('stat-confidence').textContent = (avgConf * 100).toFixed(1) + '%';
  document.getElementById('stat-top').textContent        = top;
}

function renderSpeciesChart(data) {
  const counts = {};
  data.forEach(d => { counts[d.species] = (counts[d.species] || 0) + 1; });
  const labels = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  const values = labels.map(l => counts[l]);

  if (chartSpecies) chartSpecies.destroy();
  chartSpecies = new Chart(
    document.getElementById('chart-species').getContext('2d'),
    {
      type: 'bar',
      data: { labels, datasets: [{ data: values, backgroundColor: labels.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]), borderRadius: 3, borderSkipped: false }] },
      options: {
        ...baseChartOptions('Count'),
        maintainAspectRatio: false,
        onClick: (_, elements) => { if (elements.length) openSpeciesPanel(labels[elements[0].index]); },
        onHover:  (e, el) => { e.native.target.style.cursor = el.length ? 'pointer' : 'default'; },
      },
    }
  );
}

function renderTimelineChart(data) {
  const byDate = {};
  data.forEach(d => {
    const date = d.created_at?.split('T')[0];
    if (date) byDate[date] = (byDate[date] || 0) + 1;
  });
  const labels = Object.keys(byDate).sort();
  const values = labels.map(l => byDate[l]);

  if (chartTimeline) chartTimeline.destroy();
  chartTimeline = new Chart(
    document.getElementById('chart-timeline').getContext('2d'),
    {
      type: 'line',
      data: { labels, datasets: [{ data: values, borderColor: '#5cb85c', backgroundColor: 'rgba(92,184,92,0.08)', fill: true, tension: 0.4, pointRadius: 2, pointBackgroundColor: '#5cb85c' }] },
      options: { ...baseChartOptions('Detections'), maintainAspectRatio: false },
    }
  );
}

function renderHeatmap(data) {
  const matrix = Array.from({ length: 7 }, () => new Array(24).fill(0));
  data.forEach(d => {
    if (!d.created_at) return;
    const dt = new Date(d.created_at);
    matrix[(dt.getDay() + 6) % 7][dt.getHours()]++;
  });
  const maxVal    = Math.max(...matrix.flat(), 1);
  const container = document.getElementById('heatmap-container');
  container.innerHTML = '';

  const header = document.createElement('div');
  header.className = 'heatmap-row';
  header.innerHTML = '<div class="heatmap-day-label"></div>';
  for (let h = 0; h < 24; h++) {
    const el = document.createElement('div');
    el.className   = 'heatmap-hour-label';
    el.textContent = h % 6 === 0 ? `${h}h` : '';
    header.appendChild(el);
  }
  container.appendChild(header);

  DAYS.forEach((day, di) => {
    const row = document.createElement('div');
    row.className = 'heatmap-row';
    const label = document.createElement('div');
    label.className = 'heatmap-day-label';
    label.textContent = day;
    row.appendChild(label);
    for (let h = 0; h < 24; h++) {
      const cell = document.createElement('div');
      cell.className        = 'heatmap-cell';
      cell.style.background = heatColor(matrix[di][h] / maxVal);
      cell.title            = `${day} ${String(h).padStart(2,'0')}:00 — ${matrix[di][h]} detection${matrix[di][h] !== 1 ? 's' : ''}`;
      row.appendChild(cell);
    }
    container.appendChild(row);
  });
}

function heatColor(t) {
  if (t === 0) return '#1e3020';
  return `rgb(${Math.round(30 + t * 62)},${Math.round(48 + t * 136)},${Math.round(32 + t * 60)})`;
}

function renderRecentTable(data) {
  const rows = [...data].reverse().slice(0, 50);
  document.getElementById('detections-tbody').innerHTML = rows.length
    ? rows.map(d => `
        <tr>
          <td class="td-id">${d.id ?? '—'}</td>
          <td><span class="species-tag clickable" onclick="openSpeciesPanel('${d.species}')">${d.species ?? '—'}</span></td>
          <td class="td-conf">${d.confidence != null ? (d.confidence * 100).toFixed(1) + '%' : '—'}</td>
          <td class="td-time">${fmtTime(d.created_at)}</td>
        </tr>`).join('')
    : '<tr><td colspan="4" class="empty-row">No detections yet.</td></tr>';
}

function openSpeciesPanel(species) {
  const data = filteredData.filter(d => d.species === species);
  document.getElementById('panel-species-name').textContent = species;
  document.getElementById('panel-total').textContent        = data.length.toLocaleString();

  const avgConf = data.length > 0 ? data.reduce((s, d) => s + (d.confidence ?? 0), 0) / data.length : 0;
  document.getElementById('panel-avg-conf').textContent = (avgConf * 100).toFixed(1) + '%';

  const sorted = [...data].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  document.getElementById('panel-first').textContent = sorted[0]?.created_at                    ? fmtTime(sorted[0].created_at)                    : '—';
  document.getElementById('panel-last').textContent  = sorted[sorted.length - 1]?.created_at    ? fmtTime(sorted[sorted.length - 1].created_at)    : '—';

  if (chartPanel) chartPanel.destroy();
  chartPanel = new Chart(
    document.getElementById('chart-panel').getContext('2d'),
    {
      type: 'line',
      data: {
        labels:   sorted.map(d => d.created_at?.split('T')[0] ?? ''),
        datasets: [{ data: sorted.map(d => +(d.confidence * 100).toFixed(1)), borderColor: '#5cb85c', backgroundColor: 'rgba(92,184,92,0.08)', fill: true, tension: 0.3, pointRadius: 2, pointBackgroundColor: '#5cb85c' }],
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: '#2a4230' }, ticks: { color: '#7a9e7a', maxRotation: 45, maxTicksLimit: 6 } },
          y: { grid: { color: '#2a4230' }, ticks: { color: '#7a9e7a' }, title: { display: true, text: 'Confidence %', color: '#7a9e7a', font: { size: 11 } }, min: 0, max: 100 },
        },
      },
    }
  );

  document.getElementById('species-panel').classList.add('open');
  document.getElementById('panel-overlay').classList.remove('hidden');
}

function closeSpeciesPanel() {
  document.getElementById('species-panel').classList.remove('open');
  document.getElementById('panel-overlay').classList.add('hidden');
  if (chartPanel) { chartPanel.destroy(); chartPanel = null; }
}

function exportCSV() {
  const headers = ['id','species','confidence','created_at'];
  const rows    = filteredData.map(d => [d.id ?? '', `"${(d.species ?? '').replace(/"/g,'""')}"`, d.confidence ?? '', d.created_at ?? '']);
  const csv     = [headers, ...rows].map(r => r.join(',')).join('\n');
  const url     = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  const a       = Object.assign(document.createElement('a'), { href: url, download: `hawkeye-${new Date().toISOString().split('T')[0]}.csv` });
  a.click();
  URL.revokeObjectURL(url);
}

function openSettings() {
  document.getElementById('settings-overlay').classList.remove('hidden');
  checkStatus();
}

function closeSettings() {
  document.getElementById('settings-overlay').classList.add('hidden');
}

async function checkStatus() { checkPiStatus(); checkDbStatus(); }

async function checkPiStatus() {
  const dot = document.getElementById('pi-dot'), text = document.getElementById('pi-status-text');
  dot.className = 'status-dot checking'; text.textContent = 'Checking...';
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 4000);
    await fetch(`http://${CONFIG.PI_IP}:5000/`, { signal: ctrl.signal, mode: 'no-cors' });
    clearTimeout(t);
    dot.className = 'status-dot online'; text.textContent = 'Online';
  } catch { dot.className = 'status-dot offline'; text.textContent = 'Offline or unreachable'; }
}

async function checkDbStatus() {
  const dot = document.getElementById('db-dot'), text = document.getElementById('db-status-text');
  const urlEl = document.getElementById('db-url-display');
  dot.className = 'status-dot checking'; text.textContent = 'Checking...';
  urlEl.textContent = CONFIG.SUPABASE_URL?.replace('https://', '') ?? 'Not configured';
  if (!isSupabaseConfigured()) { dot.className = 'status-dot offline'; text.textContent = 'Not configured — fill in config.js'; return; }
  try {
    const { error } = await db.from('Detections').select('id').limit(1);
    if (error) throw error;
    dot.className = 'status-dot online'; text.textContent = 'Connected';
  } catch { dot.className = 'status-dot offline'; text.textContent = 'Connection failed'; }
}

function fmtTime(ts) { return ts ? new Date(ts).toLocaleString() : '—'; }

function baseChartOptions(yLabel) {
  return {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: '#2a4230' }, ticks: { color: '#7a9e7a', maxRotation: 45 } },
      y: { grid: { color: '#2a4230' }, ticks: { color: '#7a9e7a' }, title: { display: true, text: yLabel, color: '#7a9e7a', font: { size: 11 } }, beginAtZero: true },
    },
  };
}

function setTableLoading() {
  document.getElementById('detections-tbody').innerHTML = '<tr><td colspan="4" class="empty-row">Loading...</td></tr>';
}

function setAnalyticsError(msg) {
  ['stat-total','stat-species','stat-confidence','stat-top'].forEach(id => { document.getElementById(id).textContent = '—'; });
  document.getElementById('detections-tbody').innerHTML = `<tr><td colspan="4" class="empty-row">${msg}</td></tr>`;
}

function isSupabaseConfigured() {
  return CONFIG.SUPABASE_URL && !CONFIG.SUPABASE_URL.startsWith('YOUR_') &&
         CONFIG.SUPABASE_ANON_KEY && !CONFIG.SUPABASE_ANON_KEY.startsWith('YOUR_');
}

document.getElementById('refresh-btn').addEventListener('click', loadAnalytics);
document.getElementById('export-btn').addEventListener('click', exportCSV);
document.getElementById('settings-btn').addEventListener('click', openSettings);
document.getElementById('settings-close').addEventListener('click', closeSettings);
document.getElementById('settings-overlay').addEventListener('click', e => { if (e.target === e.currentTarget) closeSettings(); });
document.getElementById('panel-close').addEventListener('click', closeSpeciesPanel);
document.getElementById('panel-overlay').addEventListener('click', closeSpeciesPanel);
document.querySelectorAll('.filter-btn').forEach(btn => btn.addEventListener('click', () => applyFilter(btn.dataset.range)));

initFeed();
loadAnalytics();
