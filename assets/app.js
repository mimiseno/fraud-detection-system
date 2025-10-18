// Frontend script for dashboard + prediction form

async function loadMetrics() {
  // Always read from API so the dashboard reflects notebook exports.
  let data = null;
  try {
    const res = await fetch('/api/metrics', { cache: 'no-store' });
    if (res.ok) data = await res.json();
  } catch (e) {
    console.warn('Metrics API failed:', e);
  }
  if (!data) {
    // Fallback: static precomputed metrics at the project root for local preview
    try {
      const res = await fetch('/metrics_precomputed.json', { cache: 'no-store' });
      if (res.ok) {
        data = await res.json();
        data.source = data.source || 'precomputed';
        showNotice('Using local precomputed metrics (fallback). Deploy to enable API.', 'info');
      }
    } catch (_) {}
  }
  if (!data) {
    showNotice('Metrics are unavailable. Ensure api/metrics_precomputed.json exists or add api/test_set_small.json and models for live metrics.', 'error');
    return;
  }
  renderSourceBadge(data.source || 'dynamic');
  showNotice(`Metrics source: ${data.source === 'precomputed' ? 'Notebook export' : data.source}`, 'info');
  renderKpis(data);
  renderGroupedBarChart(data);
  renderTable(data);
}

function pct(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return `${(v * 100).toFixed(2)}%`;
}

function renderKpis(data) {
  const kpis = document.getElementById('kpis');
  if (!kpis) return;
  const rf = data.models.find(m => m.name === 'Random Forest') || data.models[0];
  const items = [
    { label: 'Accuracy', value: pct(rf.metrics.accuracy) },
    { label: 'Precision', value: pct(rf.metrics.precision) },
    { label: 'Recall', value: pct(rf.metrics.recall) },
    { label: 'F1 Score', value: pct(rf.metrics.f1) },
  ];
  kpis.innerHTML = items.map(it => `
    <div class="rounded-lg border border-slate-200 bg-white p-3 shadow-sm hover:shadow-md transition-shadow">
      <div class="text-sm font-medium text-slate-600 mb-1">${it.label}</div>
      <div class="text-xl font-bold text-yellow-600">${it.value}</div>
    </div>
  `).join('');
}

function renderGroupedBarChart(data) {
  const mount = document.getElementById('chart');
  if (!mount) return;

  // Metrics to display and their labels
  const METRICS = [
    ['accuracy', 'Accuracy'],
    ['precision', 'Precision'],
    ['recall', 'Recall'],
    ['f1', 'F1-Score']
  ];

  // Models order and colors - updated for yellow theme
  const COLORS = {
    'Random Forest': '#F59E0B',  // amber-500 (primary - yellow theme)
    'GBM': '#10B981',            // emerald-500
    'Decision Tree': '#6366F1'   // indigo-500
  };

  // Keep only the models we care about, in this order
  const models = data.models.map(m => m.name);
  const allModels = ['Random Forest', 'GBM', 'Decision Tree'].filter(m => models.includes(m));

  // Make the chart responsive to container width
  const containerW = Math.max(480, mount.clientWidth || 620);
  const width = containerW; // pixel width
  const height = 280;
  const margin = { top: 10, right: 10, bottom: 60, left: 32 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // Layout: add padding inside each group so bars don't touch borders
  const groupWidth = innerW / METRICS.length;
  const groupPadding = 20; // left+right padding within each group
  const innerGroup = Math.max(40, groupWidth - groupPadding);
  const barGap = 8; // space between bars within a group
  // Keep bars slim for small screens
  const computedBarWidth = (innerGroup - barGap * (allModels.length - 1)) / allModels.length;
  const barWidth = Math.min(18, Math.max(8, computedBarWidth));

  const svg = [
    `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" class="block mx-auto">`,
    `<g transform="translate(${margin.left},${margin.top})">`
  ];

  // Y axis ticks (85 to 100 like the sample look)
  const ticks = [0.85, 0.90, 0.95, 1.00];
  const y = (v) => innerH - (v * innerH);
  svg.push(`<g class="text-slate-400" font-size="10">`);
  ticks.forEach(t => {
    const yy = y(t);
    svg.push(`<line x1="0" x2="${innerW}" y1="${yy}" y2="${yy}" stroke="#e5e7eb" />`);
    svg.push(`<text x="-8" y="${yy + 3}" text-anchor="end" fill="#64748b">${(t*100).toFixed(0)}</text>`);
  });
  svg.push(`</g>`);

  // Bars
  METRICS.forEach(([key, label], i) => {
    const gx = i * groupWidth + (groupWidth - innerGroup) / 2; // center inner group
    allModels.forEach((modelName, j) => {
      const model = data.models.find(m => m.name === modelName);
      if (!model) return;
      const val = Math.max(0, Math.min(1, model.metrics[key] ?? 0));
      const h = (val) * innerH;
      const x = gx + j * (barWidth + barGap);
      const yTop = innerH - h;
      const color = COLORS[modelName] || '#111827';
      svg.push(`<rect x="${x}" y="${yTop}" width="${barWidth}" height="${h}" fill="${color}" rx="2" ry="2" />`);
    });
    // x-axis label
    svg.push(`<text x="${i * groupWidth + groupWidth/2}" y="${innerH + 26}" text-anchor="middle" fill="#111827" font-size="12">${label}</text>`);
  });

  // Legend
  const legendY = innerH + 48;
  const n = Math.max(1, allModels.length);
  allModels.forEach((modelName, idx) => {
    const color = COLORS[modelName] || '#111827';
    const cx = (innerW * (idx + 0.5)) / n; // evenly spaced center positions
    const rectX = cx - 40; // small square to the left of label
    svg.push(`<rect x="${rectX}" y="${legendY - 7}" width="12" height="12" fill="${color}" rx="2"/>`);
    svg.push(`<text x="${rectX + 16}" y="${legendY + 0}" fill="#111827" font-size="12" dominant-baseline="middle">${modelName}</text>`);
  });

  svg.push(`</g></svg>`);
  mount.innerHTML = svg.join('');
}

function renderTable(data) {
  const rows = document.getElementById('metrics-rows');
  if (!rows) return;
  rows.innerHTML = data.models.map((m, index) => {
    const isRF = m.name === 'Random Forest';
    const bgClass = isRF ? 'bg-yellow-50' : 'hover:bg-slate-50';
    const textClass = isRF ? 'font-semibold text-slate-800' : 'text-slate-700';
    return `
    <tr class="${bgClass} transition-colors duration-150">
      <td class="py-4 ${textClass}">
        <div class="flex items-center gap-2">
          ${isRF ? '<div class="h-2 w-2 rounded-full bg-yellow-500"></div>' : ''}
          ${m.name}
          ${isRF ? '<span class="text-xs bg-yellow-500 text-white px-2 py-0.5 rounded-full font-medium">PRIMARY</span>' : ''}
        </div>
      </td>
      <td class="py-4 font-medium">${pct(m.metrics.accuracy)}</td>
      <td class="py-4 font-medium">${pct(m.metrics.precision)}</td>
      <td class="py-4 font-medium">${pct(m.metrics.recall)}</td>
      <td class="py-4 font-medium">${pct(m.metrics.f1)}</td>
      <td class="py-4 font-medium">${pct(m.metrics.roc_auc)}</td>
    </tr>
  `}).join('');
  
  // Render business impact analysis
  renderBusinessImpact(data.models);
}

function renderBusinessImpact(models) {
  const container = document.getElementById('business-impact-grid');
  if (!container) return;
  
  container.innerHTML = models.map(model => {
    const metrics = model.metrics;
    
    // Business impact calculations (10,000 transactions, 1% fraud rate)
    const totalTransactions = 10000;
    const actualFraud = 100;
    const actualLegit = totalTransactions - actualFraud;
    
    // Calculate confusion matrix values from precision and recall
    const truePositives = Math.round(actualFraud * metrics.recall);
    const falseNegatives = actualFraud - truePositives;
    const falsePositives = Math.round((truePositives / metrics.precision) - truePositives);
    const totalFlagged = truePositives + falsePositives;
    
    // Performance indicators with simplified color scheme
    let performanceColor, performanceText, textColorClass;
    if (metrics.f1 >= 0.9) {
      performanceColor = 'bg-emerald-50 border-emerald-200/60';
      performanceText = 'Excellent';
      textColorClass = 'text-emerald-600';
    } else if (metrics.f1 >= 0.8) {
      performanceColor = 'bg-yellow-50 border-yellow-200/60';
      performanceText = 'Very Good';
      textColorClass = 'text-yellow-600';
    } else if (metrics.f1 >= 0.7) {
      performanceColor = 'bg-blue-50 border-blue-200/60';
      performanceText = 'Good';
      textColorClass = 'text-blue-600';
    } else {
      performanceColor = 'bg-red-50 border-red-200/60';
      performanceText = 'Needs Improvement';
      textColorClass = 'text-red-600';
    }
    
    return `
      <div class="rounded-lg border ${performanceColor} p-4 shadow-sm hover:shadow-md transition-shadow">
        <div class="mb-3 flex items-center justify-between">
          <h4 class="text-lg font-bold ${textColorClass}">${model.name}</h4>
        </div>
        
        <div class="mb-4">
          <div class="text-sm font-semibold text-slate-700 mb-1">Overall Performance</div>
          <div class="text-base font-bold ${textColorClass}">${performanceText}</div>
        </div>
        
        <div class="space-y-3 text-sm">
          <div class="rounded-md bg-white/60 p-3 border border-white/40">
            <div class="text-xs font-bold uppercase tracking-wide text-slate-600 mb-2">FLAGGED TRANSACTIONS</div>
            <div class="text-xs text-slate-600 mb-2">
              Out of <span class="font-semibold text-slate-800">${totalFlagged.toLocaleString()}</span> flagged as fraud:
            </div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-emerald-600 font-medium">✓ ${truePositives} genuine fraud</span>
              <span class="text-red-500 font-medium">✗ ${falsePositives} false alarms</span>
            </div>
            <div class="text-xs text-slate-500">
              Precision: <span class="font-semibold">${pct(metrics.precision)}</span>
            </div>
          </div>
          
          <div class="rounded-md bg-white/60 p-3 border border-white/40">
            <div class="text-xs font-bold uppercase tracking-wide text-slate-600 mb-2">FRAUD DETECTION</div>
            <div class="text-xs text-slate-600 mb-2">
              Out of <span class="font-semibold text-slate-800">${actualFraud}</span> actual fraud cases:
            </div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-emerald-600 font-medium">✓ ${truePositives} detected</span>
              <span class="text-red-500 font-medium">✗ ${falseNegatives} missed</span>
            </div>
            <div class="text-xs text-slate-500">
              Recall: <span class="font-semibold">${pct(metrics.recall)}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderSourceBadge(source) {
  // Attach a tiny badge to the dashboard card header when available
  const h2 = document.querySelector('h2.text-lg.font-semibold');
  if (!h2) return;
  const badge = document.createElement('span');
  badge.className = 'ml-2 align-middle rounded-full bg-slate-100 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-600';
  let label = 'Live';
  if (source === 'static') label = 'Static';
  if (source === 'precomputed') label = 'Precomputed';
  badge.textContent = label;
  h2.appendChild(badge);
}

function showNotice(text, type='info') {
  const host = document.getElementById('notice');
  if (!host) return;
  const base = 'mb-2 rounded-lg px-3 py-2 text-sm';
  const cls = type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-50 text-slate-700 border border-slate-200';
  host.innerHTML = `<div class="${base} ${cls}">${text}</div>`;
}

function bindPredictForm() {
  const form = document.getElementById('tx-form');
  if (!form) return;
  
  // Handle transaction type dropdown
  const typeSelect = document.getElementById('transactionType');
  const cashOutInput = form.querySelector('input[name="isCashOut"]');
  const transferInput = form.querySelector('input[name="isTransfer"]');
  
  if (typeSelect && cashOutInput && transferInput) {
    typeSelect.addEventListener('change', (e) => {
      if (e.target.value === 'cashout') {
        cashOutInput.value = '1';
        transferInput.value = '0';
      } else if (e.target.value === 'transfer') {
        cashOutInput.value = '0';
        transferInput.value = '1';
      } else if (e.target.value === 'payment') {
        cashOutInput.value = '0';
        transferInput.value = '0';
      }
    });
  }
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate transaction type selection
    const typeSelect = document.getElementById('transactionType');
    if (!typeSelect.value) {
      alert('Please select a transaction type.');
      typeSelect.focus();
      return;
    }
    
    // Validate all required fields
    const requiredFields = form.querySelectorAll('input[required]');
    for (const field of requiredFields) {
      if (!field.value.trim()) {
        alert(`Please fill in the ${field.name} field.`);
        field.focus();
        return;
      }
    }
    
    const fd = new FormData(form);
    const formData = Object.fromEntries([...fd.entries()]);
    
    // Get form values and convert to numbers
    const amount = parseFloat(formData.amount) || 0;
    const oldbalanceOrg = parseFloat(formData.oldbalanceOrg) || 0;
    const newbalanceOrig = parseFloat(formData.newbalanceOrig) || 0;
    const oldbalanceDest = parseFloat(formData.oldbalanceDest) || 0;
    const newbalanceDest = parseFloat(formData.newbalanceDest) || 0;
    
    // Calculate derived features
    const errorBalanceOrig = newbalanceOrig + amount - oldbalanceOrg;
    const errorBalanceDest = oldbalanceDest + amount - newbalanceDest;
    
    // Get transaction type from dropdown
    const transactionType = document.getElementById('transactionType').value;
    
    // Create payload with all required features for the model
    const payload = {
      step: 1,
      amount: amount,
      oldbalanceOrg: oldbalanceOrg,
      newbalanceOrig: newbalanceOrig,
      oldbalanceDest: oldbalanceDest,
      newbalanceDest: newbalanceDest,
      errorBalanceOrig: errorBalanceOrig,
      errorBalanceDest: errorBalanceDest,
      type_CASH_OUT: transactionType === 'cashout' ? 1 : 0,
      type_DEBIT: transactionType === 'debit' ? 1 : 0,
      type_PAYMENT: transactionType === 'payment' ? 1 : 0,
      type_TRANSFER: transactionType === 'transfer' ? 1 : 0
    };

    const resultEl = document.getElementById('result');
    const probEl = document.getElementById('prob');
    resultEl.textContent = 'Predicting...';
    probEl.textContent = '';

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      // Check if response is ok
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`API Error (${res.status}): ${errorText || 'Unknown error'}`);
      }
      
      // Check if response has content
      const contentType = res.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const responseText = await res.text();
        throw new Error(`Expected JSON response, got: ${contentType}. Response: ${responseText}`);
      }
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Prediction failed');
      resultEl.innerHTML = `
        <div class="text-sm">Prediction</div>
        <div class="mt-1 text-2xl font-semibold ${data.label === 'Fraud' ? 'text-red-600' : 'text-emerald-700'}">${data.label}</div>
      `;
      probEl.textContent = `Fraud probability: ${pct(data.probability)}`;
    } catch (err) {
      console.error('Prediction error:', err);
      resultEl.innerHTML = `<div class="text-red-600">Error: ${err.message}</div>`;
      probEl.textContent = '';
    }
  });
}

window.addEventListener('DOMContentLoaded', () => {
  loadMetrics();
  bindPredictForm();
});
