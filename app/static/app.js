/* ══════════════════════════════════════════════════════════════
   BreastGuard AI — Application Logic
   ══════════════════════════════════════════════════════════════ */

const API = 'http://localhost:5000';

// ─── State ────────────────────────────────────────────────────
let uploadedFile   = null;
let currentResult  = null;
let currentExamId  = null;
let probChart      = null;

// ─── Theme ────────────────────────────────────────────────────
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('bgai-theme', isDark ? 'light' : 'dark');
  if (probChart) rebuildChart(currentResult);
}

(function initTheme() {
  const saved = localStorage.getItem('bgai-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

// ─── Tab Navigation ──────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
  document.getElementById(`panel-${name}`).classList.add('active');
  document.getElementById(`tab-${name}`).classList.add('active');
  if (name === 'samples') loadSamples();
}

// ─── Upload Zone ─────────────────────────────────────────────
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('uploadZone').classList.add('drag-over');
}
function handleDragLeave(e) {
  document.getElementById('uploadZone').classList.remove('drag-over');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('uploadZone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) setUploadedFile(file);
}
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) setUploadedFile(file);
}

function setUploadedFile(file) {
  uploadedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    const img   = document.getElementById('previewImg');
    const label = document.getElementById('previewLabel');
    const grid  = document.getElementById('previewGrid');
    img.src = e.target.result;
    label.textContent = file.name;
    grid.style.display = 'flex';
  };
  reader.readAsDataURL(file);
  document.getElementById('analyzeBtn').disabled = false;
  document.getElementById('resultCard').classList.add('hidden');
  toast('✅ Image loaded — ready to analyze', 'success');
}

// ─── Analyze Uploaded Image ───────────────────────────────────
async function analyzeUpload() {
  if (!uploadedFile) return;
  showLoading('Analyzing Mammogram');
  currentExamId = null;

  try {
    await runLoadingSteps();

    const formData = new FormData();
    formData.append('image', uploadedFile);

    const resp = await fetch(`${API}/api/predict/image`, {
      method: 'POST',
      body: formData
    });
    if (!resp.ok) throw new Error(await resp.text());
    const result = await resp.json();

    hideLoading();
    currentResult = result;
    displayResult(result);
    toast(`🔬 Classification: ${result.label}`, 'success');
  } catch (err) {
    hideLoading();
    toast(`❌ Error: ${err.message}`, 'error');
  }
}

// ─── Load Sample Patients ─────────────────────────────────────
async function loadSamples() {
  const grid = document.getElementById('samplesGrid');
  grid.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const resp  = await fetch(`${API}/api/samples`);
    const data  = await resp.json();
    renderSamples(data.samples);
  } catch (e) {
    grid.innerHTML = `<p style="color:var(--malignant);padding:16px">⚠ Could not load samples. Make sure the server is running.</p>`;
  }
}

function renderSamples(samples) {
  const grid = document.getElementById('samplesGrid');
  grid.innerHTML = '';

  const names = ['Sarah Johnson', 'Maria Chen', 'Emma Williams', 'Lena Fischer'];
  const ages  = [47, 53, 41, 62];
  const icons = ['🟢 Normal', '🟡 Benign', '🟢 Normal', '🟡 Benign'];

  samples.forEach((s, i) => {
    const thumbs = s.images.slice(0, 4).map(img => {
      const view = img.view.replace('-', '_');
      return `<img class="sample-thumb"
              src="${API}/api/samples/${s.id}/image/${img.view.replace('-', '_')}"
              alt="${img.view}"
              onerror="this.outerHTML='<div class=\\'sample-thumb-placeholder\\'>🩻</div>'"
              />`;
    }).join('');

    const card = document.createElement('div');
    card.className = 'sample-patient-card';
    card.innerHTML = `
      <div class="sample-thumb-grid">${thumbs}</div>
      <div class="sample-info">
        <div class="sample-patient-id">Patient ${s.patient_id}</div>
        <div style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">${names[i]}, Age ${ages[i]}</div>
        <div class="sample-views">📷 Views: L-CC · L-MLO · R-CC · R-MLO</div>
        <button class="sample-analyze-btn" onclick="analyzeSample('${s.id}', '${names[i]}', ${ages[i]})">
          🔬 Analyze This Exam
        </button>
      </div>`;
    grid.appendChild(card);
  });
}

async function analyzeSample(examId, patientName, patientAge) {
  showTab('analyze');
  showLoading('Analyzing Sample Exam');
  currentExamId = examId;

  // Auto-fill patient form
  document.getElementById('patientName').value    = patientName;
  document.getElementById('patientAge').value     = patientAge;
  document.getElementById('patientID').value      = `PT-${parseInt(examId) + 1000}`;
  document.getElementById('patientGender').value  = 'Female';
  document.getElementById('facilityName').value   = 'NYU Langone Health - Breast Imaging';
  document.getElementById('patientPhysician').value = 'Dr. Krzysztof J. Geras';

  // Set DOB approx
  const birthYear = new Date().getFullYear() - patientAge;
  document.getElementById('patientDOB').value = `${birthYear}-06-15`;

  try {
    await runLoadingSteps();
    const resp = await fetch(`${API}/api/analyze/exam/${examId}`, { method: 'POST' });
    if (!resp.ok) throw new Error(await resp.text());
    const result = await resp.json();

    hideLoading();
    currentResult = result;
    displayResult(result);

    // Show the first sample image in preview
    const img   = document.getElementById('previewImg');
    const grid  = document.getElementById('previewGrid');
    const label = document.getElementById('previewLabel');
    img.src     = `${API}/api/samples/${examId}/image/L_CC`;
    img.onerror = () => { img.src = ''; };
    label.textContent = `Patient ${parseInt(examId) + 1000} — L-CC View`;
    grid.style.display = 'flex';

    toast(`🔬 Sample exam analyzed: ${result.label}`, 'success');
  } catch (err) {
    hideLoading();
    toast(`❌ ${err.message}`, 'error');
  }
}

// ─── Display Results ─────────────────────────────────────────
function displayResult(result) {
  const { label, probabilities: probs, risk_score, confidence, risk_level, recommendation } = result;

  // Show card
  const card = document.getElementById('resultCard');
  card.classList.remove('hidden');
  card.classList.add('result-reveal');
  setTimeout(() => card.classList.remove('result-reveal'), 800);

  // Colors
  const colors = {
    Normal:    { main: '#10B981', bg: 'bg-normal',    icon: '✅' },
    Benign:    { main: '#F59E0B', bg: 'bg-benign',    icon: '⚠️' },
    Malignant: { main: '#EF4444', bg: 'bg-malignant', icon: '🚨' },
  };
  const cls = colors[label] || colors.Benign;

  // Banner
  const banner = document.getElementById('classificationBanner');
  banner.className = `classification-banner ${cls.bg}`;
  document.getElementById('classIcon').textContent  = cls.icon;
  document.getElementById('clsLabel').textContent  = label;
  document.getElementById('clsLabel').style.color  = cls.main;
  document.getElementById('clsSub').textContent    = `AI Classification · ${new Date().toLocaleDateString()}`;
  document.getElementById('confidencePill').textContent = `Confidence: ${(confidence*100).toFixed(1)}%`;

  // Badge
  const badge = document.getElementById('resultBadge');
  badge.textContent  = label.toUpperCase();
  badge.style.color  = cls.main;
  badge.style.borderColor = cls.main;

  // Probability bars (animated)
  const pn = (probs.normal    || 0) * 100;
  const pb = (probs.benign    || 0) * 100;
  const pm = (probs.malignant || 0) * 100;

  setTimeout(() => {
    document.getElementById('barNormal').style.width    = `${pn.toFixed(1)}%`;
    document.getElementById('barBenign').style.width    = `${pb.toFixed(1)}%`;
    document.getElementById('barMalignant').style.width = `${pm.toFixed(1)}%`;

    document.getElementById('pNormal').textContent    = `${pn.toFixed(1)}%`;
    document.getElementById('pBenign').textContent    = `${pb.toFixed(1)}%`;
    document.getElementById('pMalignant').textContent = `${pm.toFixed(1)}%`;
  }, 100);

  // Risk gauge
  const riskPct = Math.round((risk_score || 0) * 100);
  setTimeout(() => {
    document.getElementById('riskGaugeFill').style.width = `${riskPct}%`;
    document.getElementById('riskScoreNum').textContent   = `${riskPct}/100`;
    document.getElementById('chartPct').textContent       = `${riskPct}%`;
  }, 150);

  // Risk badge
  const riskBadge = document.getElementById('riskLevelBadge');
  const riskStyles = { Low: '#10B981', Moderate: '#F59E0B', High: '#EF4444', 'Very High': '#DC2626' };
  riskBadge.textContent          = risk_level || 'N/A';
  riskBadge.style.background     = (riskStyles[risk_level] || '#94A3B8') + '22';
  riskBadge.style.color          = riskStyles[risk_level]  || '#94A3B8';
  riskBadge.style.border         = `1px solid ${(riskStyles[risk_level] || '#94A3B8')}66`;

  // Recommendation
  document.getElementById('recText').textContent = recommendation || 'Consult your physician.';

  // Build chart
  rebuildChart(result);

  // Scroll to results
  setTimeout(() => {
    document.getElementById('resultCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 300);
}

function rebuildChart(result) {
  if (!result) return;
  const { probabilities: probs } = result;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#94A3B8' : '#475569';

  const ctx = document.getElementById('probChart').getContext('2d');
  if (probChart) { probChart.destroy(); probChart = null; }

  probChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Normal', 'Benign', 'Malignant'],
      datasets: [{
        data: [
          ((probs.normal    || 0) * 100).toFixed(1),
          ((probs.benign    || 0) * 100).toFixed(1),
          ((probs.malignant || 0) * 100).toFixed(1),
        ],
        backgroundColor: ['rgba(16,185,129,0.85)', 'rgba(245,158,11,0.85)', 'rgba(239,68,68,0.85)'],
        borderColor:     ['#10B981', '#F59E0B', '#EF4444'],
        borderWidth: 2,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: textColor, font: { size: 11, family: 'Inter' },
            padding: 12, boxWidth: 12, boxHeight: 12,
          }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.raw}%`
          }
        }
      },
      animation: {
        animateRotate: true,
        duration: 1200,
        easing: 'easeInOutQuart'
      }
    }
  });
}

// ─── Generate PDF Report ─────────────────────────────────────
async function generateReport() {
  if (!currentResult) {
    toast('❌ No analysis result. Analyze an image first.', 'error');
    return;
  }

  const patientName = document.getElementById('patientName').value.trim() || 'Unknown Patient';
  const btn = document.getElementById('generateReportBtn');
  btn.disabled = true;
  btn.innerHTML = '<span>⏳</span> Generating...';

  const payload = {
    patient: {
      name:      patientName,
      dob:       document.getElementById('patientDOB').value       || '',
      age:       document.getElementById('patientAge').value        || '',
      gender:    document.getElementById('patientGender').value     || 'Female',
      id:        document.getElementById('patientID').value         || `PT-${Date.now().toString().slice(-6)}`,
      physician: document.getElementById('patientPhysician').value  || '',
      contact:   document.getElementById('patientContact').value    || '',
    },
    result: currentResult,
    exam: {
      type:            'Mammography Screening (4-View)',
      facility:        document.getElementById('facilityName').value || 'AI Diagnostic Center',
      date:            new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
      processing_time: '< 2 seconds',
    }
  };

  try {
    const resp = await fetch(`${API}/api/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) throw new Error(await resp.text());

    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    const safePatient = patientName.replace(/\s+/g, '_');
    const today = new Date().toISOString().split('T')[0];
    a.href     = url;
    a.download = `BreastCancerReport_${safePatient}_${today}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast('📄 PDF Report downloaded!', 'success');
  } catch (err) {
    toast(`❌ Report failed: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>📄</span> Generate PDF Report';
  }
}

// ─── Reset Analysis ───────────────────────────────────────────
function resetAnalysis() {
  uploadedFile  = null;
  currentResult = null;
  currentExamId = null;
  document.getElementById('fileInput').value       = '';
  document.getElementById('previewGrid').style.display = 'none';
  document.getElementById('previewImg').src         = '';
  document.getElementById('analyzeBtn').disabled    = true;
  document.getElementById('resultCard').classList.add('hidden');
  if (probChart) { probChart.destroy(); probChart = null; }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  toast('🔄 Ready for new analysis', 'success');
}

// ─── Loading Steps ────────────────────────────────────────────
async function runLoadingSteps() {
  const steps    = ['lstep-1', 'lstep-2', 'lstep-3', 'lstep-4'];
  const durations = [400, 600, 700, 400];
  for (let i = 0; i < steps.length; i++) {
    if (i > 0) document.getElementById(steps[i-1]).className = 'lstep done';
    document.getElementById(steps[i]).className = 'lstep active';
    await sleep(durations[i]);
  }
}

function showLoading(title = 'Processing') {
  document.getElementById('loadingTitle').textContent = title;
  ['lstep-1','lstep-2','lstep-3','lstep-4'].forEach(id => {
    document.getElementById(id).className = 'lstep';
  });
  document.getElementById('loadingOverlay').classList.remove('hidden');
}
function hideLoading() {
  document.getElementById('loadingOverlay').classList.add('hidden');
}

// ─── Toast Notifications ──────────────────────────────────────
function toast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'slideInToast 0.3s ease reverse forwards';
    setTimeout(() => t.remove(), 300);
  }, 3500);
}

// ─── Utilities ────────────────────────────────────────────────
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─── Navbar scroll effect ─────────────────────────────────────
window.addEventListener('scroll', () => {
  const nav = document.getElementById('navbar');
  nav.style.boxShadow = window.scrollY > 10
    ? '0 4px 32px rgba(0,0,0,0.4)'
    : 'none';
});

// ─── Boot ────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  // Health check
  fetch(`${API}/health`)
    .then(r => r.json())
    .then(() => toast('✅ Server connected', 'success'))
    .catch(() => toast('⚠ Server offline — start server with: python app/server.py', 'error'));
});
