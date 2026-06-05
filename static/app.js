// app.js — UI 控制层（Task 07 补充 WebSocket 实时逻辑）

// ── DOM refs ──
const avatarWrap      = document.getElementById('avatarWrap');
const bgGlow          = document.getElementById('bgGlow');
const aiStatus        = document.getElementById('aiStatus');
const aiCaption       = document.getElementById('aiCaption');
const userSubWrap     = document.getElementById('userSubtitleWrap');
const userSubText     = document.getElementById('userSubtitleText');
const btnMic          = document.getElementById('btnMic');
const btnInterrupt    = document.getElementById('btnInterrupt');
const btnEnd          = document.getElementById('btnEnd');
const btnHistory      = document.getElementById('btnHistory');
const corrPopup       = document.getElementById('correctionPopup');
const corrClose       = document.getElementById('corrClose');
const historyDrawer   = document.getElementById('historyDrawer');
const drawerClose     = document.getElementById('drawerClose');
const drawerMask      = document.getElementById('drawerMask');
const drawerList      = document.getElementById('drawerList');
const reportBanner    = document.getElementById('reportBanner');
const btnReport       = document.getElementById('btnReport');

// ── 阶段配置 ──
const STAGES = ['intro', 'job_qa', 'behavioral', 'candidate_qa'];
const STAGE_LABELS = { intro:'自我介绍', job_qa:'岗位问答', behavioral:'行为面试', candidate_qa:'反问环节' };

function setStage(stageName) {
  const idx = STAGES.indexOf(stageName);
  document.querySelectorAll('.dot').forEach((dot, i) => {
    dot.classList.remove('active', 'done');
    if (i < idx) dot.classList.add('done');
    if (i === idx) dot.classList.add('active');
  });
  document.getElementById('stageLabelText').textContent = STAGE_LABELS[stageName] || stageName;
}

// ── 头像状态切换 ──
function setAvatarState(state) {
  // state: 'idle' | 'ai-speaking' | 'user-speaking'
  avatarWrap.classList.remove('ai-speaking', 'user-speaking');
  bgGlow.classList.remove('ai-speaking', 'user-speaking');
  if (state === 'ai-speaking') {
    avatarWrap.classList.add('ai-speaking');
    bgGlow.classList.add('ai-speaking');
    aiStatus.textContent = 'AI 正在说话...';
    aiStatus.classList.add('active');
    btnInterrupt.disabled = false;
  } else if (state === 'user-speaking') {
    avatarWrap.classList.add('user-speaking');
    bgGlow.classList.add('user-speaking');
    aiStatus.textContent = '正在聆听...';
    aiStatus.classList.add('active');
    btnInterrupt.disabled = true;
  } else {
    aiStatus.textContent = '等待开始';
    aiStatus.classList.remove('active');
    btnInterrupt.disabled = true;
  }
}

// ── AI 字幕 ──
function setAiCaption(text) {
  aiCaption.textContent = text;
}

function appendAiCaption(token) {
  aiCaption.textContent += token;
}

// ── 用户实时字幕 ──
function setUserSubtitle(text) {
  if (!text) {
    userSubWrap.style.display = 'none';
    return;
  }
  userSubWrap.style.display = 'flex';
  userSubText.textContent = text;
}

// ── 纠错弹窗 ──
const correctionHistory = [];

function showCorrection({ original, suggestion, explanation }) {
  document.getElementById('corrOriginal').textContent    = original;
  document.getElementById('corrSuggestion').textContent  = suggestion;
  document.getElementById('corrExplanation').textContent = explanation;
  corrPopup.style.display = 'block';

  // 同时存入历史
  correctionHistory.push({ original, suggestion, explanation });
  renderHistory();
}

corrClose.addEventListener('click', () => { corrPopup.style.display = 'none'; });

// ── 纠错历史抽屉 ──
function renderHistory() {
  if (correctionHistory.length === 0) {
    drawerList.innerHTML = '<p class="drawer-empty">暂无纠错记录</p>';
    return;
  }
  drawerList.innerHTML = correctionHistory.map(c => `
    <div class="drawer-item">
      <div class="di-wrong">${c.original}</div>
      <div class="di-right">→ ${c.suggestion}</div>
      <div class="di-note">${c.explanation}</div>
    </div>
  `).join('');
}

btnHistory.addEventListener('click', () => {
  renderHistory();
  historyDrawer.style.display = 'flex';
  drawerMask.style.display = 'block';
});
drawerClose.addEventListener('click', closeDrawer);
drawerMask.addEventListener('click', closeDrawer);
function closeDrawer() {
  historyDrawer.style.display = 'none';
  drawerMask.style.display = 'none';
}

// ── 报告横幅 ──
function showReportBanner(reportPath) {
  btnReport.href = reportPath;
  reportBanner.style.display = 'flex';
}

// ── 结束会话 ──
btnEnd.addEventListener('click', () => {
  if (confirm('确认结束本次会话？')) {
    // Task 10 补充：发送 session_end 信号给后端
    console.log('[TODO] 发送结束信号 — Task 10 实现');
  }
});

// ── 麦克风（Task 07 接管真正的录音逻辑） ──
btnMic.addEventListener('mousedown', () => {
  btnMic.classList.add('recording');
  setAvatarState('user-speaking');
  setUserSubtitle('...');
});

btnMic.addEventListener('mouseup', () => {
  btnMic.classList.remove('recording');
  setAvatarState('idle');
  setUserSubtitle('');
});

// 移动端 touchstart/touchend
btnMic.addEventListener('touchstart', (e) => { e.preventDefault(); btnMic.dispatchEvent(new Event('mousedown')); });
btnMic.addEventListener('touchend',   (e) => { e.preventDefault(); btnMic.dispatchEvent(new Event('mouseup')); });

// ── 打断 ──
btnInterrupt.addEventListener('click', () => {
  setAvatarState('idle');
  setAiCaption('');
  // Task 07 补充：发送 interrupt 消息
  console.log('[TODO] 打断 AI — Task 07 实现');
});

// ── 初始化 ──
setStage('intro');
setAvatarState('idle');
