/**
 * PostHarvestSaver — Frontend Logic
 * Handles crop selection, API calls, risk visualization,
 * history management, filtering, and sorting.
 */

// ──────────────────────────────────────────────
// State
// ──────────────────────────────────────────────
let analysisHistory = JSON.parse(localStorage.getItem('phs_history') || '[]');
let currentFilter = 'all';
let currentSort = 'newest';

// ──────────────────────────────────────────────
// DOM References
// ──────────────────────────────────────────────
const cropBtns       = document.querySelectorAll('.crop-btn');
const cropMinis      = document.querySelectorAll('.crop-card-mini');
const selectedCropEl = document.getElementById('selectedCrop');
const districtSelect = document.getElementById('districtSelect');
const analyzeBtn     = document.getElementById('analyzeBtn');
const errorBox       = document.getElementById('errorBox');
const errorMsg       = document.getElementById('errorMsg');
const resultsPanel   = document.getElementById('resultsPanel');
const loadingState   = document.getElementById('loadingState');
const resultsContent = document.getElementById('resultsContent');
const filterBar      = document.getElementById('filterBar');
const historySection = document.getElementById('historySection');
const historyGrid    = document.getElementById('historyGrid');
const clearHistoryBtn= document.getElementById('clearHistoryBtn');
const sortSelect     = document.getElementById('sortSelect');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');

// ──────────────────────────────────────────────
// Crop Selection
// ──────────────────────────────────────────────
function selectCrop(cropKey) {
  selectedCropEl.value = cropKey;
  cropBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.crop === cropKey));
  cropMinis.forEach(mini => {
    mini.style.transform = mini.dataset.crop === cropKey ? 'scale(1.15)' : '';
    mini.style.filter = mini.dataset.crop === cropKey ? 'drop-shadow(0 0 6px rgba(22,163,74,0.5))' : '';
  });
  hideError();
}

cropBtns.forEach(btn => btn.addEventListener('click', () => selectCrop(btn.dataset.crop)));
cropMinis.forEach(mini => mini.addEventListener('click', () => {
  selectCrop(mini.dataset.crop);
  document.querySelector('.form-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}));

// ──────────────────────────────────────────────
// Error Handling
// ──────────────────────────────────────────────
function showError(msg) {
  errorMsg.textContent = msg;
  errorBox.style.display = 'flex';
  errorBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
  errorBox.style.display = 'none';
}

// ──────────────────────────────────────────────
// Risk Color Helpers
// ──────────────────────────────────────────────
const RISK_COLORS = {
  LOW:      { bg: '#f0fdf4', border: '#86efac', text: '#166534', pill_bg: '#dcfce7', pill_text: '#166534' },
  MEDIUM:   { bg: '#fefce8', border: '#fde047', text: '#713f12', pill_bg: '#fef08a', pill_text: '#713f12' },
  HIGH:     { bg: '#fff7ed', border: '#fdba74', text: '#7c2d12', pill_bg: '#fed7aa', pill_text: '#7c2d12' },
  CRITICAL: { bg: '#fef2f2', border: '#fca5a5', text: '#7f1d1d', pill_bg: '#fee2e2', pill_text: '#7f1d1d' },
};

// ──────────────────────────────────────────────
// Main Analyze Function
// ──────────────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
  hideError();

  const crop = selectedCropEl.value;
  const district = districtSelect.value;

  if (!crop) {
    showError('Please select a crop before analyzing.');
    return;
  }
  if (!district) {
    showError('Please select a district before analyzing.');
    return;
  }

  // Show results panel with loading
  resultsPanel.style.display = 'block';
  loadingState.style.display = 'flex';
  resultsContent.style.display = 'none';
  analyzeBtn.disabled = true;
  analyzeBtn.querySelector('.btn-text').textContent = 'Analyzing...';

  resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ crop, district }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.error || 'An unexpected error occurred. Please try again.');
    }

    renderResults(data);
    saveToHistory(data);

  } catch (err) {
    loadingState.style.display = 'none';
    resultsPanel.style.display = 'none';
    showError(err.message);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.querySelector('.btn-text').textContent = 'Analyze Spoilage Risk';
  }
});

// ──────────────────────────────────────────────
// Render Results
// ──────────────────────────────────────────────
function renderResults(data) {
  const { crop, crop_icon, district, region, weather, risk, recommendations, optimal_conditions, timestamp } = data;
  const colors = RISK_COLORS[risk.level];

  // Header
  document.getElementById('resultCropIcon').textContent = crop_icon;
  document.getElementById('resultCropName').textContent = crop;
  document.getElementById('resultLocation').textContent = `📍 ${district} District, ${region} Province`;
  document.getElementById('resultTimestamp').textContent = `Analyzed: ${timestamp}`;

  // Risk Meter
  const pct = risk.score;
  document.getElementById('riskFill').style.transform = `scaleX(${(100 - pct) / 100})`;
  document.getElementById('riskThumb').style.left = `${pct}%`;
  document.getElementById('riskThumb').style.borderColor = colors.text;

  const riskBadge = document.getElementById('riskBadge');
  riskBadge.style.background = colors.bg;
  riskBadge.style.borderColor = colors.border;
  riskBadge.style.color = colors.text;

  document.getElementById('riskEmoji').textContent = risk.emoji;
  document.getElementById('riskLevelText').textContent = risk.level;
  document.getElementById('riskScore').textContent = `${risk.score}/100`;
  document.getElementById('riskActionLabel').textContent = risk.label;

  // Weather Cards
  document.getElementById('wTemp').textContent      = `${weather.temperature}°C`;
  document.getElementById('wHumidity').textContent   = `${weather.humidity}%`;
  document.getElementById('wRainfall').textContent   = `${weather.rainfall}mm`;
  document.getElementById('wWind').textContent       = `${weather.wind_speed} km/h`;
  document.getElementById('weatherDesc').textContent = `☁️ ${weather.description} · Feels like ${weather.feels_like}°C`;

  // Optimal vs Current
  document.getElementById('optimalTemp').textContent     = `✅ Ideal: ${optimal_conditions.temp}`;
  document.getElementById('currentTemp').textContent     = `Now: ${weather.temperature}°C`;
  document.getElementById('optimalHumidity').textContent = `✅ Ideal: ${optimal_conditions.humidity}`;
  document.getElementById('currentHumidity').textContent = `Now: ${weather.humidity}%`;

  // Risk Factors
  const factorsList = document.getElementById('factorsList');
  factorsList.innerHTML = risk.factors.map(f => `<li>${f}</li>`).join('');

  // Recommendations
  const recsList = document.getElementById('recsList');
  recsList.innerHTML = recommendations.map(r => `<li>${r}</li>`).join('');

  // Show results
  loadingState.style.display = 'none';
  resultsContent.style.display = 'block';
}

// ──────────────────────────────────────────────
// New Analysis Button
// ──────────────────────────────────────────────
newAnalysisBtn.addEventListener('click', () => {
  resultsPanel.style.display = 'none';
  document.querySelector('.form-panel').scrollIntoView({ behavior: 'smooth' });
});

// ──────────────────────────────────────────────
// History Management
// ──────────────────────────────────────────────
function saveToHistory(data) {
  const entry = {
    id: Date.now(),
    crop: data.crop,
    crop_icon: data.crop_icon,
    district: data.district,
    risk_level: data.risk.level,
    risk_score: data.risk.score,
    risk_emoji: data.risk.emoji,
    timestamp: data.timestamp,
    weather: data.weather,
  };

  analysisHistory.unshift(entry);
  // Keep max 20 entries
  if (analysisHistory.length > 20) analysisHistory = analysisHistory.slice(0, 20);
  localStorage.setItem('phs_history', JSON.stringify(analysisHistory));

  renderHistory();
  filterBar.style.display = 'block';
}

function renderHistory() {
  if (analysisHistory.length === 0) {
    historySection.style.display = 'none';
    filterBar.style.display = 'none';
    return;
  }

  historySection.style.display = 'block';

  // Apply sort
  let sorted = [...analysisHistory];
  if (currentSort === 'oldest') sorted.reverse();
  else if (currentSort === 'risk_high') sorted.sort((a, b) => b.risk_score - a.risk_score);
  else if (currentSort === 'risk_low')  sorted.sort((a, b) => a.risk_score - b.risk_score);

  historyGrid.innerHTML = sorted.map(entry => {
    const colors = RISK_COLORS[entry.risk_level];
    const hidden = (currentFilter !== 'all' && entry.risk_level !== currentFilter) ? 'hidden' : '';
    return `
      <div class="history-card ${hidden}" data-risk="${entry.risk_level}" data-id="${entry.id}">
        <div class="history-card-top">
          <div class="history-crop-info">
            <span class="history-crop-icon">${entry.crop_icon}</span>
            <div>
              <div class="history-crop-name">${entry.crop}</div>
              <div class="history-district">📍 ${entry.district}</div>
            </div>
          </div>
          <span class="history-risk-pill" style="background:${colors.pill_bg};color:${colors.pill_text}">
            ${entry.risk_emoji} ${entry.risk_level}
          </span>
        </div>
        <div class="history-card-bottom">
          <span class="history-score" style="color:${colors.text}">${entry.risk_score}<small>/100</small></span>
          <span class="history-time">${entry.timestamp}</span>
        </div>
      </div>
    `;
  }).join('');
}

// Filter Buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    currentFilter = btn.dataset.filter;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderHistory();
  });
});

// Sort Select
sortSelect.addEventListener('change', () => {
  currentSort = sortSelect.value;
  renderHistory();
});

// Clear History
clearHistoryBtn.addEventListener('click', () => {
  if (confirm('Clear all analysis history?')) {
    analysisHistory = [];
    localStorage.removeItem('phs_history');
    historySection.style.display = 'none';
    filterBar.style.display = 'none';
  }
});

// ──────────────────────────────────────────────
// Init — Restore History on Load
// ──────────────────────────────────────────────
if (analysisHistory.length > 0) {
  renderHistory();
  filterBar.style.display = 'block';
}
