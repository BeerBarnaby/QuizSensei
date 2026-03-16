'use strict';

/* ══════════════════════════════════════════════════════════════════════
   API CLIENT
   ══════════════════════════════════════════════════════════════════════ */
const API = {
  base: '/api/v1',

  async request(method, path, body, isFormData = false) {
    const opts = { method };
    if (body) {
      if (isFormData) { opts.body = body; }
      else { opts.headers = { 'Content-Type': 'application/json' }; opts.body = JSON.stringify(body); }
    }
    const res = await fetch(`${API.base}${path}`, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    return res.json();
  },

  listDocuments: () => API.request('GET', '/documents/'),
  uploadDocument: (fd) => API.request('POST', '/documents/upload', fd, true),
  extractDocument: (id) => API.request('POST', `/documents/${id}/extract`),
  getPreview: (id) => API.request('GET', `/documents/${id}/preview`),
  analyzeDocument: (id) => API.request('POST', `/documents/${id}/analyze`),
  getAnalysis: (id) => API.request('GET', `/documents/${id}/analysis`),
  generateQuestions: (id, body) => API.request('POST', `/documents/${id}/generate-questions`, body),
  submitAnswer: (body) => API.request('POST', '/exams/submit', body),
  deleteDocument: (id) => API.request('DELETE', `/documents/${id}`),
};

/* ══════════════════════════════════════════════════════════════════════
   STATE
   ══════════════════════════════════════════════════════════════════════ */
const state = {
  primaryDocId: null,   // The main doc used for analyze + generate
  extraDocIds: [],     // Extra docs whose text will be merged during generation
  analysisResult: null,   // Last Agent 1 result for primary doc
  questions: [],
  answers: {},
  graderOutputs: {},
  submitted: false,
  isProcessing: false,
};

/* ══════════════════════════════════════════════════════════════════════
   ELEMENTS
   ══════════════════════════════════════════════════════════════════════ */
const $ = id => document.getElementById(id);
const el = {
  fileInput: $('fileInput'),
  docList: $('docList'),
  refreshDocs: $('refreshDocs'),
  emptyState: $('emptyState'),
  activePanel: $('activePanel'),
  panelTitle: $('panelTitle'),
  panelBadge: $('panelBadge'),
  charCount: $('charCount'),
  btnGenerate: $('btnGenerate'),
  btnRetry: $('btnRetry'),
  quizArea: $('quizArea'),
  quizResult: $('quizResult'),
  resultScore: $('resultScore'),
  resultMsg: $('resultMsg'),
  statusToast: $('statusToast'),
  statusText: $('statusText'),
};

/* ══════════════════════════════════════════════════════════════════════
   TOAST HELPERS
   ══════════════════════════════════════════════════════════════════════ */
function showToast(msg, isError = false) {
  el.statusText.textContent = msg;
  el.statusToast.style.background = isError ? '#dc2626' : '#1e293b';
  el.statusToast.classList.remove('hidden');
}
function hideToast(delay = 0) { setTimeout(() => el.statusToast.classList.add('hidden'), delay); }
function escHtml(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* ══════════════════════════════════════════════════════════════════════
   STAGE SWITCHER
   ══════════════════════════════════════════════════════════════════════ */
function switchStage(stage) {
  const stages = ['extraction', 'analysis', 'quiz'];
  const curIdx = stages.indexOf(stage);

  document.querySelectorAll('.step').forEach(s => {
    s.classList.remove('active', 'completed');
  });
  stages.forEach((s, idx) => {
    const stepEl = $(`step-${s}`);
    if (!stepEl) return;
    if (idx < curIdx) stepEl.classList.add('completed');
    else if (idx === curIdx) stepEl.classList.add('active');
  });

  document.querySelectorAll('.stage-content').forEach(v => v.classList.remove('active'));
  const target = $(`view-${stage}`);
  if (target) target.classList.add('active');

  // Populate Stage 3 preview whenever user enters it
  if (stage === 'quiz') populateQuizStage();
}

/**
 * Populate Stage 3 content preview and level verification
 */
async function populateQuizStage() {
  // 1. Content preview - load primary doc text
  const previewBox = $('contentPreviewBox');
  const badge = $('docCountBadge');
  if (previewBox && state.primaryDocId) {
    const totalDocs = 1 + state.extraDocIds.length;
    if (badge) badge.textContent = `${totalDocs} เอกสาร`;
    try {
      const pv = await API.getPreview(state.primaryDocId);
      let combinedText = `=== เอกสารหลัก: ${state.primaryDocId} ===\n${pv.preview_text || '(ไม่มีข้อมูล)'}`;
      for (const extra of state.extraDocIds) {
        try {
          const epv = await API.getPreview(extra);
          combinedText += `\n\n=== เอกสารสำรอง: ${extra} ===\n${epv.preview_text || '(ไม่มีข้อมูล)'}`;
        } catch { combinedText += `\n\n=== เอกสารสำรอง: ${extra} === (ยังไม่ได้สกัดข้อความ)`; }
      }
      previewBox.textContent = combinedText;
    } catch {
      previewBox.textContent = 'ไม่สามารถโหลดตัวอย่างเนื้อหาได้';
    }
  }

  // 2. Level verification banner
  checkLevelMismatch();
}

/**
 * Warns if the user-selected audience differs from Agent 1's recommendation
 */
function checkLevelMismatch() {
  const warning = $('levelMismatchWarning');
  const agentLevelEl = $('agentSuggestedLevel');
  if (!warning || !state.analysisResult) return;

  const agentLevel = state.analysisResult.suggested_learner_level || '';
  const userLevel = $('qAudience')?.value || '';

  if (agentLevelEl) agentLevelEl.textContent = agentLevel || '(ไม่ทราบ)';

  if (agentLevel && userLevel && agentLevel !== userLevel) {
    warning.classList.remove('hidden');
  } else {
    warning.classList.add('hidden');
  }
}

/* ══════════════════════════════════════════════════════════════════════
   DOC LIST & UPLOAD
   ══════════════════════════════════════════════════════════════════════ */
let _cachedDocs = [];

async function loadDocumentList() {
  try {
    _cachedDocs = await API.listDocuments();
  } catch { _cachedDocs = []; }
  renderDocList();
}

function renderDocList() {
  if (!_cachedDocs.length) {
    el.docList.innerHTML = '<li class="doc-list-empty">ยังไม่มีเอกสาร</li>';
    return;
  }
  const icon = ext => ({ '.pdf': '📄', '.docx': '📝', '.doc': '📝', '.txt': '📃' }[ext] || '📎');

  el.docList.innerHTML = _cachedDocs.map(d => {
    const isPrimary = d.document_id === state.primaryDocId;
    const isExtra = state.extraDocIds.includes(d.document_id);
    let cls = 'doc-item';
    if (isPrimary) cls += ' active';
    else if (isExtra) cls += ' selected-extra';

    return `
      <li class="${cls}" data-id="${escHtml(d.document_id)}">
        <div class="doc-icon">${icon(d.extension)}</div>
        <div style="overflow:hidden; flex:1;">
          <div class="doc-name">${escHtml(d.filename)}</div>
          <div class="doc-meta">${(d.size_bytes / 1024).toFixed(1)} KB${isPrimary ? ' • <strong style="color:var(--primary)">หลัก</strong>' : isExtra ? ' • <strong style="color:var(--success)">สำรอง</strong>' : ''}</div>
        </div>
        <div class="doc-actions">
          ${isExtra ? `<div class="doc-check">✓</div>` : ''}
          <button class="doc-delete-btn" title="ลบเอกสาร" data-del-id="${escHtml(d.document_id)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"/></svg>
          </button>
        </div>
      </li>`;
  }).join('');

  el.docList.querySelectorAll('.doc-item').forEach(item => {
    item.addEventListener('click', () => handleDocClick(item.dataset.id));
  });

  el.docList.querySelectorAll('.doc-delete-btn').forEach(btn => {
    btn.addEventListener('click', (e) => handleDeleteDoc(e, btn.dataset.delId));
  });
}

async function handleDeleteDoc(e, docId) {
  e.stopPropagation();

  if (!confirm(`ยืนยันการลบเอกสาร "${docId}" หรือไม่? ข้อมูลที่วิเคราะห์และข้อสอบที่ประเมินแล้วจะถูกลบไปด้วย`)) {
    return;
  }

  showToast(`⏳ กำลังลบเอกสาร ${docId}...`);
  try {
    await API.deleteDocument(docId);
    showToast(`✅ ลบเอกสารสำเร็จ`, false);

    // Clear state if the deleted doc is primary or extra
    if (state.primaryDocId === docId) {
      state.primaryDocId = null;
      state.analysisResult = null;
      state.extraDocIds = [];
      el.emptyState.classList.remove('hidden');
      el.activePanel.classList.add('hidden');
    } else {
      const idx = state.extraDocIds.indexOf(docId);
      if (idx !== -1) {
        state.extraDocIds.splice(idx, 1);
        updateSufficiencyBanner();
      }
    }

    await loadDocumentList();
    hideToast(2000);
  } catch (err) {
    showToast(`❌ ลบเอกสารไม่สำเร็จ: ${err.message}`, true);
    hideToast(3500);
  }
}

/**
 * Click logic:
 * - If no primary doc → set as primary, start pipeline
 * - If clicking a different doc and primary is set → toggle it as "extra" supplementary doc
 * - If clicking the current primary doc → do nothing (already selected)
 */
function handleDocClick(docId) {
  if (state.isProcessing) return;

  if (!state.primaryDocId || docId === state.primaryDocId) {
    // Set or reselect as primary
    if (docId !== state.primaryDocId) {
      state.primaryDocId = docId;
      state.extraDocIds = [];
      state.analysisResult = null;
      renderDocList();
      startPrimaryPipeline(docId);
    }
  } else {
    // Toggle as supplementary doc
    const idx = state.extraDocIds.indexOf(docId);
    if (idx === -1) {
      state.extraDocIds.push(docId);
      ensureExtracted(docId); // Extract in background if needed
    } else {
      state.extraDocIds.splice(idx, 1);
    }
    renderDocList();
    updateSufficiencyBanner();
  }
}

// Make sure a supplementary doc is extracted (silently)
async function ensureExtracted(docId) {
  try {
    await API.getPreview(docId);
  } catch {
    try {
      showToast(`กำลัง Extract เอกสารสำรอง...`);
      await API.extractDocument(docId);
      hideToast(1500);
    } catch (e) {
      console.warn(`Failed to extract extra doc ${docId}:`, e.message);
    }
  }
}

async function handleUpload(file) {
  if (!file) return;
  showToast(`กำลังอัปโหลด ${file.name}...`);
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res = await API.uploadDocument(fd);
    hideToast(500);
    await loadDocumentList();
    // Auto-select the newly uploaded file as primary
    state.primaryDocId = res.saved_as;
    state.extraDocIds = [];
    renderDocList();
    showPanel(res.saved_as);
    await startPrimaryPipeline(res.saved_as);
  } catch (e) {
    showToast(`❌ อัปโหลดไม่สำเร็จ: ${e.message}`, true);
    hideToast(3500);
  }
}

/* ══════════════════════════════════════════════════════════════════════
   MAIN PANEL
   ══════════════════════════════════════════════════════════════════════ */
function showPanel(docId) {
  el.emptyState.classList.add('hidden');
  el.activePanel.classList.remove('hidden');
  el.panelTitle.textContent = docId;
  const ext = (docId.split('.').pop() || 'FILE').toUpperCase();
  el.panelBadge.textContent = ext;
  el.charCount.textContent = '—';

  // Reset quiz area
  state.questions = []; state.answers = {}; state.graderOutputs = {}; state.submitted = false;
  el.quizArea.innerHTML = '';
  el.quizResult.classList.add('hidden');

  switchStage('extraction');
}

/* ══════════════════════════════════════════════════════════════════════
   AUTOMATED PIPELINE (Primary Doc)
   Steps: Extract (if needed) → Analyze (if needed) → Show analysis panel
   ══════════════════════════════════════════════════════════════════════ */
async function startPrimaryPipeline(docId) {
  if (state.isProcessing) return;
  state.isProcessing = true;
  showPanel(docId);
  switchStage('extraction');

  try {
    // ── STEP 1: Extract ──────────────────────────────────────────
    showToast('⏳ กำลังสกัดข้อความ...');
    let preview;
    try {
      preview = await API.getPreview(docId);
    } catch {
      await API.extractDocument(docId);
      preview = await API.getPreview(docId);
    }
    renderExtraction(preview);
    hideToast(500);

    // ── STEP 2: Analyze (Agent 1) ────────────────────────────────
    switchStage('analysis');
    showToast('🤖 Agent 1 กำลังวิเคราะห์เนื้อหา...');
    let analysis;
    try {
      analysis = await API.getAnalysis(docId);
      // Re-analyze if stale or incomplete
      if (!analysis || !analysis.topic) throw new Error('stale');
    } catch {
      analysis = await API.analyzeDocument(docId);
    }
    state.analysisResult = analysis;
    renderAnalysis(analysis);
    showToast('✅ วิเคราะห์สำเร็จ', false);
    hideToast(2000);

  } catch (err) {
    showToast(`❌ ${err.message}`, true);
    hideToast(4000);
  } finally {
    state.isProcessing = false;
  }
}

/* ══════════════════════════════════════════════════════════════════════
   RENDERERS
   ══════════════════════════════════════════════════════════════════════ */
function renderExtraction(data) {
  const charCount = data.char_count || 0;
  el.charCount.textContent = charCount.toLocaleString();
  $('extractedTextPreview').textContent = data.preview_text || '(ไม่มีตัวอักษรที่สกัดได้)';
}

function renderAnalysis(data) {
  const parent = $('analysisResult');
  if (!parent) return;
  const ok = data.analysis_status === 'success';
  const kw = (data.keywords_found || []).map(k => `<span class="badge-premium badge-blue">${escHtml(k)}</span>`).join(' ');

  parent.innerHTML = `
    <div class="heading-outfit" style="margin-bottom:20px; font-size:18px;">Agent 1 – ผลวิเคราะห์เนื้อหา</div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:20px;">
      <div class="glass-card" style="margin-bottom:0; padding:16px; border-left:4px solid var(--primary);">
        <div style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">หัวข้อหลัก</div>
        <div style="font-weight:700; font-size:15px; color:var(--primary); margin-top:4px;">${escHtml(data.topic?.replace(/_/g, ' ') || '-')}</div>
      </div>
      <div class="glass-card" style="margin-bottom:0; padding:16px;">
        <div style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">หัวข้อย่อย</div>
        <div style="font-weight:600; font-size:14px; margin-top:4px;">${escHtml(data.subtopic?.replace(/_/g, ' ') || '-')}</div>
      </div>
    </div>

    <div class="glass-card" style="border-left:4px solid var(--purple); margin-bottom:16px;">
      <div style="display:flex; justify-content:space-between; align-items:start;">
        <div>
          <div style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">กลุ่มเป้าหมายที่เหมาะสม</div>
          <div style="font-size:22px; font-weight:700; color:var(--purple); margin-top:4px;">${escHtml(data.suggested_learner_level || '-')}</div>
        </div>
        <span class="badge-premium badge-purple">Agent 1: แนะนำ</span>
      </div>
      <div style="font-size:13px; color:var(--text-muted); margin-top:10px; line-height:1.6;">${escHtml(data.learner_level_reason || '')}</div>
    </div>

    <div id="sufficiencyBanner"></div>

    ${kw ? `<div style="margin-top:16px;"><div style="font-size:11px; color:var(--text-dim); text-transform:uppercase; margin-bottom:8px;">คำสำคัญที่พบ</div><div style="display:flex; flex-wrap:wrap; gap:6px;">${kw}</div></div>` : ''}
  `;

  // Sync audience dropdown
  if (ok && data.suggested_learner_level) {
    const sel = $('qAudience');
    if (sel) Array.from(sel.options).forEach(opt => { if (opt.value === data.suggested_learner_level) opt.selected = true; });
  }

  updateSufficiencyBanner();
}

/**
 * Shows a sufficiency banner based on:
 * - analysis result
 * - how many extra docs have been added
 */
function updateSufficiencyBanner() {
  const banner = $('sufficiencyBanner');
  if (!banner || !state.analysisResult) return;

  const sufficient = state.analysisResult.content_sufficiency;
  const extraCount = state.extraDocIds.length;
  const goBtn = $('btnGoToGenerate');

  if (sufficient) {
    banner.innerHTML = `
      <div class="diag-box" style="border-color:var(--success); background:#f0fdf4;">
        <div class="diag-title" style="color:var(--success);">✅ เนื้อหาเพียงพอสำหรับสร้างข้อสอบ</div>
        <div class="diag-text">${escHtml(state.analysisResult.sufficiency_reason || '')}</div>
      </div>`;
    if (goBtn) goBtn.disabled = false;
  } else if (extraCount > 0) {
    banner.innerHTML = `
      <div class="diag-box" style="border-color:var(--warning); background:#fffbeb;">
        <div class="diag-title" style="color:var(--warning);">⚠️ เนื้อหาในเอกสารหลักยังไม่ครบ แต่ระบบจะรวม ${extraCount} เอกสารสำรองด้วย</div>
        <div class="diag-text">คุณสามารถดำเนินการต่อได้ ข้อสอบจะอิงจากเนื้อหาทั้งหมด ${1 + extraCount} ไฟล์</div>
      </div>`;
    if (goBtn) goBtn.disabled = false;
  } else {
    banner.innerHTML = `
      <div class="diag-box" style="border-color:var(--danger); background:#fff1f2;">
        <div class="diag-title" style="color:var(--danger);">❌ เนื้อหาไม่เพียงพอ – ต้องการเอกสารเพิ่มเติม</div>
        <div class="diag-text">${escHtml(state.analysisResult.sufficiency_reason || '')}</div>
        <div style="margin-top:12px; padding:10px; background:#fee2e2; border-radius:8px; font-size:13px;">
          <strong>👈 วิธีแก้ไข:</strong> คลิกเลือก <strong>เอกสารอื่นๆ ในรายการซ้ายมือ</strong> เพื่อเพิ่มเป็น "เอกสารสำรอง" แล้วระบบจะรวมเนื้อหาให้อัตโนมัติ
        </div>
      </div>`;
    if (goBtn) goBtn.disabled = true;
  }
}

/* ══════════════════════════════════════════════════════════════════════
   QUIZ – GENERATE (Agent 2 + 3)
   ══════════════════════════════════════════════════════════════════════ */
async function handleGenerate() {
  if (!state.primaryDocId || state.isProcessing) return;

  el.btnGenerate.disabled = true;
  el.btnGenerate.innerHTML = `<span>⏳ กำลังสร้าง...</span>`;
  el.quizArea.innerHTML = `<div class="glass-card" style="text-align:center; color:var(--text-muted); padding:40px;">Agent 2 กำลังออกแบบข้อสอบ... Agent 3 กำลังตรวจสอบคุณภาพ...</div>`;

  const body = {
    number_of_questions: parseInt($('qCount').value) || 3,
    target_audience_level: $('qAudience').value || 'วัยทำงาน',
    difficulty_filter: $('qDifficulty').value || 'medium',
    additional_document_ids: state.extraDocIds,
  };

  try {
    const res = await API.generateQuestions(state.primaryDocId, body);
    state.questions = res.questions || [];

    if (!state.questions.length) {
      el.quizArea.innerHTML = `<div class="diag-box" style="border-color:var(--warning);">
        <div class="diag-title" style="color:var(--warning);">ข้อสอบทั้งหมดถูก Agent 3 ปฏิเสธ (${res.total_rejected || 0} ข้อ)</div>
        <div class="diag-text">ลองเพิ่มจำนวนข้อสอบ เปลี่ยนระดับความยาก หรือเพิ่มเอกสารสำรองเพิ่มเติมครับ</div>
      </div>`;
    } else {
      renderQuiz(res);
    }
  } catch (err) {
    el.quizArea.innerHTML = `<div class="diag-box" style="border-color:var(--danger);">
      <div class="diag-title" style="color:var(--danger);">❌ ไม่สามารถสร้างข้อสอบได้</div>
      <div class="diag-text">${escHtml(err.message)}</div>
    </div>`;
  } finally {
    el.btnGenerate.disabled = false;
    el.btnGenerate.innerHTML = `<span>🚀 สร้างข้อสอบ (Agent 2 & 3)</span>`;
  }
}

function renderQuiz(res) {
  const total = state.questions.length;
  const rejectedNote = res.total_rejected > 0
    ? `<div style="font-size:12px; color:var(--text-dim); margin-bottom:16px;">Agent 3 ผ่าน ${total} ข้อ, ปฏิเสธ ${res.total_rejected} ข้อ${state.extraDocIds.length ? ` (รวมจาก ${1 + state.extraDocIds.length} เอกสาร)` : ''}</div>`
    : '';

  el.quizArea.innerHTML = rejectedNote + state.questions.map((q, i) => `
    <div class="q-card" id="qcard-${q.question_id}">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <strong style="color:var(--primary);">ข้อที่ ${i + 1}</strong>
        <div style="display:flex; gap:6px;">
          <span class="badge-premium badge-blue">${escHtml(q.difficulty)}</span>
          ${q.bloom_level ? `<span class="badge-premium badge-purple">🎓 ${escHtml(q.bloom_level)}</span>` : ''}
        </div>
      </div>
      <p style="font-size:16px; font-weight:600; line-height:1.6; margin-bottom:20px;">${escHtml(q.stem)}</p>
      <div class="choice-grid">
        ${q.choices.map(c => `
          <button class="choice-item" data-qid="${q.question_id}" data-key="${c.key}">
            <div style="font-weight:700; opacity:0.5; min-width:18px;">${c.key}</div>
            <div>${escHtml(c.text)}</div>
          </button>`).join('')}
      </div>
      <div id="diag-${q.question_id}" class="hidden"></div>
      ${q.design_reasoning ? `
        <details style="margin-top:14px;">
          <summary style="font-size:12px; color:var(--text-dim); cursor:pointer; user-select:none;">💡 ทำไมถึงมีคำถามนี้? (Agent 2)</summary>
          <div style="margin-top:8px; font-size:13px; color:var(--text-muted); padding:12px; background:#f8fafc; border-radius:8px; line-height:1.6;">${escHtml(q.design_reasoning)}</div>
        </details>` : ''}
    </div>
  `).join('') + `
    <button id="btnSubmitQuiz" class="btn-premium btn-primary" style="width:100%; height:52px; font-size:15px; margin-top:8px;">
      📝 ส่งคำตอบ
    </button>`;

  // Attach choice listeners
  document.querySelectorAll('.choice-item').forEach(btn => {
    btn.onclick = () => {
      if (state.submitted) return;
      const { qid, key } = btn.dataset;
      state.answers[qid] = key;
      document.querySelectorAll(`.choice-item[data-qid="${qid}"]`).forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      // Update submit button text
      const answered = Object.keys(state.answers).length;
      const sbtn = $('btnSubmitQuiz');
      if (sbtn) sbtn.textContent = `📝 ส่งคำตอบ (ตอบแล้ว ${answered}/${total} ข้อ)`;
    };
  });

  $('btnSubmitQuiz').onclick = handleSubmitQuiz;
}

/* ══════════════════════════════════════════════════════════════════════
   QUIZ – SUBMIT (Agent 4)
   ══════════════════════════════════════════════════════════════════════ */
async function handleSubmitQuiz() {
  const total = state.questions.length;
  const answered = Object.keys(state.answers).length;

  if (answered < total) {
    showToast(`กรุณาตอบให้ครบ (ตอบแล้ว ${answered}/${total} ข้อ)`, true);
    hideToast(2500);
    return;
  }

  showToast('🤖 Agent 4 กำลังตรวจคำตอบ...');
  state.submitted = true;

  let score = 0;
  for (const q of state.questions) {
    try {
      const out = await API.submitAnswer({
        question_id: q.question_id,
        selected_choice_key: state.answers[q.question_id],
        user_id: 'guest',
      });
      state.graderOutputs[q.question_id] = out;
      if (out.is_correct) score++;
      renderDiagnostic(q, out);
    } catch {
      // Fallback: deterministic grading from local data
      const key = state.answers[q.question_id];
      const isCorrect = key === q.correct_answer;
      if (isCorrect) score++;
      renderDiagnostic(q, {
        is_correct: isCorrect,
        correct_answer: q.correct_answer,
        diagnostic_message: isCorrect ? `✓ ถูกต้อง! ${q.rationale_for_correct_answer || ''}` : `✗ คำตอบที่ถูกต้องคือ ${q.correct_answer}\n${q.rationale_for_correct_choices || ''}`,
        misconception_identified: null,
        suggested_review_topic: null,
      });
    }
  }

  // Disable all submit buttons
  document.querySelectorAll('.choice-item').forEach(b => b.disabled = true);
  $('btnSubmitQuiz')?.remove();

  const pct = Math.round((score / total) * 100);
  el.resultScore.textContent = `${pct}%`;
  el.resultMsg.textContent = pct >= 80 ? '🎉 ยอดเยี่ยม! คุณเข้าใจเนื้อหานี้ดีมาก'
    : pct >= 50 ? '👍 ดี ยังมีบางหัวข้อที่ควรทบทวน'
      : '📖 ลองทบทวนเนื้อหาก่อนทำใหม่นะครับ';
  el.quizResult.classList.remove('hidden');
  el.quizResult.scrollIntoView({ behavior: 'smooth' });
  hideToast();
}

function renderDiagnostic(q, data) {
  const box = $(`diag-${q.question_id}`);
  if (!box) return;

  // Mark choices
  document.querySelectorAll(`.choice-item[data-qid="${q.question_id}"]`).forEach(btn => {
    if (btn.dataset.key === q.correct_answer) btn.classList.add('correct');
    else if (btn.dataset.key === state.answers[q.question_id]) btn.classList.add('incorrect');
  });

  box.innerHTML = `
    <div class="diag-box" style="border-color:${data.is_correct ? 'var(--success)' : 'var(--danger)'}; background:${data.is_correct ? '#f0fdf4' : '#fff1f2'};">
      <div class="diag-title" style="color:${data.is_correct ? 'var(--success)' : 'var(--danger)'};">
        ${data.is_correct ? '✨ ถูกต้อง!' : '❌ ยังไม่ถูก'}
      </div>
      <div class="diag-text">${escHtml(data.diagnostic_message || '').replace(/\n/g, '<br>')}</div>
      ${data.suggested_review_topic ? `<div style="margin-top:8px; font-size:12px; color:var(--primary);">🔖 ทบทวนหัวข้อ: <strong>${escHtml(data.suggested_review_topic)}</strong></div>` : ''}
    </div>`;
  box.classList.remove('hidden');
}

/* ══════════════════════════════════════════════════════════════════════
   INIT
   ══════════════════════════════════════════════════════════════════════ */
el.fileInput.onchange = e => { handleUpload(e.target.files[0]); el.fileInput.value = ''; };
el.refreshDocs.onclick = loadDocumentList;
el.btnGenerate.onclick = handleGenerate;
el.btnRetry.onclick = () => {
  state.questions = []; state.answers = {}; state.graderOutputs = {}; state.submitted = false;
  el.quizArea.innerHTML = '';
  el.quizResult.classList.add('hidden');
};
$('btnRedo').onclick = () => {
  if (state.primaryDocId) {
    state.analysisResult = null;
    state.extraDocIds = [];
    renderDocList();
    startPrimaryPipeline(state.primaryDocId);
  }
};

loadDocumentList();
