const { createClient } = supabase;
const db = createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);

const CHART_COLORS = [
  '#5cb85c','#4db6ac','#42a5f5','#ab47bc',
  '#ffa726','#ef5350','#26c6da','#d4e157',
];
const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

let chartSpecies  = null;
let chartTimeline = null;

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;

    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    btn.classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');

    if (tab === 'feed')      { initFeed(); }
    else                     { stopFeed(); }
    if (tab === 'analytics') { loadAnalytics(); }
    if (tab === 'settings')  { checkStatus(); }
  });
});

function initFeed() {
  const img     = document.getElementById('video-feed');
  const offline = document.getElementById('feed-offline');
  const badge   = document.getElementById('stream-badge');

  badge.textContent = 'Connecting...';
  badge.className   = 'status-badge connecting';
  offline.classList.add('hidden');

  img.onload = () => {
    badge.textContent = '● Live';
    badge.className   = 'status-badge live';
    offline.classList.add('hidden');
  };

  img.onerror = () => {
    badge.textContent = '○ Offline';
    badge.className   = 'status-badge offline';
    offline.classList.remove('hidden');
  };

  img.src = CONFIG.PI_STREAM_URL;
}

function stopFeed() {
  const img = document.getElementById('video-feed');
  img.src = '';
}

async function loadAnalytics() {
  setTableLoading();

  if (!isSupabaseConfigured()) {
    setAnalyticsError('Add your Supabase credentials to config.js');
    return;
  }

  const { data, error } = await db
    .from('Detections')
    .select('*')
    .order('created_at');

  if (error || !data) {
    setAnalyticsError('Could not reach database');
    return;
  }

  renderStats(data);
  renderSpeciesChart(data);
  renderTimelineChart(data);
  renderHeatmap(data);
  renderRecentTable(data);
}

function renderStats(data) {
  const total   = data.length;
  const species = [...new Set(data.map(d => d.species))];
  const avgConf = total > 0
    ? data.reduce((s, d) => s + (d.confidence ?? 0), 0) / total
    : 0;

  const counts = {};
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
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: labels.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
          borderRadius: 4,
          borderSkipped: false,
        }],
      },
      options: baseChartOptions('Count'),
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
      data: {
        labels,
        datasets: [{
          data: values,
          borderColor: '#5cb85c',
          backgroundColor: 'rgba(92,184,92,0.08)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: '#5cb85c',
        }],
      },
      options: baseChartOptions('Detections'),
    }
  );
}

function renderHeatmap(data) {
  const matrix = Array.from({ length: 7 }, () => new Array(24).fill(0));
  data.forEach(d => {
    if (!d.created_at) return;
    const dt  = new Date(d.created_at);
    const day = (dt.getDay() + 6) % 7;
    matrix[day][dt.getHours()]++;
  });

  const maxVal = Math.max(...matrix.flat(), 1);
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
    label.className   = 'heatmap-day-label';
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
  const r = Math.round(30  + t * (92  - 30));
  const g = Math.round(48  + t * (184 - 48));
  const b = Math.round(32  + t * (92  - 32));
  return `rgb(${r},${g},${b})`;
}

function renderRecentTable(data) {
  const rows = [...data].reverse().slice(0, 50);
  document.getElementById('detections-tbody').innerHTML = rows.length
    ? rows.map(d => `
        <tr>
          <td class="td-id">${d.id ?? '—'}</td>
          <td><span class="species-tag">${d.species ?? '—'}</span></td>
          <td class="td-conf">${d.confidence != null ? (d.confidence * 100).toFixed(1) + '%' : '—'}</td>
          <td class="td-time">${fmtTime(d.created_at)}</td>
        </tr>`).join('')
    : '<tr><td colspan="4" class="empty-row">No detections yet.</td></tr>';
}

function fmtTime(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleString();
}

function baseChartOptions(yLabel) {
  return {
    responsive: true,
    maintainAspectRatio: true,
    plugins: { legend: { display: false } },
    scales: {
      x: {
        grid:  { color: '#2a4230' },
        ticks: { color: '#7a9e7a', maxRotation: 45 },
      },
      y: {
        grid:  { color: '#2a4230' },
        ticks: { color: '#7a9e7a' },
        title: { display: true, text: yLabel, color: '#7a9e7a', font: { size: 11 } },
        beginAtZero: true,
      },
    },
  };
}

function setTableLoading() {
  document.getElementById('detections-tbody').innerHTML =
    '<tr><td colspan="4" class="empty-row">Loading...</td></tr>';
}

function setAnalyticsError(msg) {
  ['stat-total','stat-species','stat-confidence','stat-top']
    .forEach(id => { document.getElementById(id).textContent = '—'; });
  document.getElementById('detections-tbody').innerHTML =
    `<tr><td colspan="4" class="empty-row">${msg}</td></tr>`;
}

async function checkStatus() {
  checkPiStatus();
  checkDbStatus();
}

async function checkPiStatus() {
  const dot  = document.getElementById('pi-dot');
  const text = document.getElementById('pi-status-text');
  dot.className  = 'status-dot checking';
  text.textContent = 'Checking...';

  try {
    const ctrl = new AbortController();
    const t    = setTimeout(() => ctrl.abort(), 4000);
    await fetch(`http://${CONFIG.PI_IP}:5000/`, { signal: ctrl.signal, mode: 'no-cors' });
    clearTimeout(t);
    dot.className    = 'status-dot online';
    text.textContent = 'Online';
  } catch {
    dot.className    = 'status-dot offline';
    text.textContent = 'Offline or unreachable';
  }
}

async function checkDbStatus() {
  const dot    = document.getElementById('db-dot');
  const text   = document.getElementById('db-status-text');
  const urlEl  = document.getElementById('db-url-display');
  dot.className    = 'status-dot checking';
  text.textContent = 'Checking...';
  urlEl.textContent = CONFIG.SUPABASE_URL?.replace('https://', '') ?? 'Not configured';

  if (!isSupabaseConfigured()) {
    dot.className    = 'status-dot offline';
    text.textContent = 'Not configured — fill in config.js';
    return;
  }

  try {
    const { error } = await db.from('Detections').select('id').limit(1);
    if (error) throw error;
    dot.className    = 'status-dot online';
    text.textContent = 'Connected';
  } catch {
    dot.className    = 'status-dot offline';
    text.textContent = 'Connection failed';
  }
}

function isSupabaseConfigured() {
  return (
    CONFIG.SUPABASE_URL      && !CONFIG.SUPABASE_URL.startsWith('YOUR_') &&
    CONFIG.SUPABASE_ANON_KEY && !CONFIG.SUPABASE_ANON_KEY.startsWith('YOUR_')
  );
}

document.getElementById('refresh-btn').addEventListener('click', loadAnalytics);
document.getElementById('check-status-btn').addEventListener('click', checkStatus);

initFeed();
