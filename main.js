// ════════════════════════════════════════════════
// TELEGRAM WEB APP
// ════════════════════════════════════════════════
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.disableClosingConfirmation?.();
}

let questions = [];
let answers   = [];
let current   = 0;
let score     = 0;
let answered  = false;
let meta      = {};

const DEMO = [
  { id:1,  t:"Fe'lning necha zamonlari bor?",            a:"2 ta",    b:"3 ta",    c:"4 ta",   d:"5 ta",              ok:"B", img:"" },
  { id:2,  t:"Qaysi so'z olmosh turkumiga kiradi?",      a:"kitob",   b:"men",     c:"yaxshi", d:"yugurmoq",          ok:"B", img:"" },
  { id:3,  t:"O'zbek tilida unli tovushlar soni nechta?",a:"5",       b:"6",       c:"7",      d:"8",                 ok:"B", img:"" },
  { id:4,  t:"Ko'plik qo'shimchasi qaysi?",              a:"-ning",   b:"-lar",    c:"-ga",    d:"-dan",              ok:"B", img:"" },
  { id:5,  t:"Antonim nima?",                            a:"Ma'nodosh so'zlar", b:"Qarama-qarshi ma'noli so'zlar", c:"Shakldosh so'zlar", d:"Ko'p ma'noli so'zlar", ok:"B", img:"" },
];

async function loadQuestionsFromHash() {
  showLoader(true);
  const params = new URLSearchParams(window.location.search);
  const hash   = params.get('data') || window.location.hash.slice(1);

  if (!hash) {
    console.warn('Data yo\'q — demo ishlatiladi');
    questions = DEMO;
    meta      = { subject:'onatili', category:'aralash', difficulty:'easy', is_attestation:false };
    initTest();
    showLoader(false);
    return;
  }

  try {
    const b64    = hash.replace(/-/g, '+').replace(/_/g, '/');
    const binary = atob(b64);
    const bytes  = Uint8Array.from(binary, c => c.charCodeAt(0));

    const ds     = new DecompressionStream('deflate');
    const writer = ds.writable.getWriter();
    const reader = ds.readable.getReader();
    writer.write(bytes);
    writer.close();

    const chunks = [];
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
    }

    const total = chunks.reduce((s, c) => s + c.length, 0);
    const out   = new Uint8Array(total);
    let   off   = 0;
    for (const c of chunks) { out.set(c, off); off += c.length; }

    const parsed = JSON.parse(new TextDecoder('utf-8').decode(out));

    if (Array.isArray(parsed)) {
      questions = parsed;
      meta      = {};
    } else {
      questions = parsed.questions || parsed;
      meta      = parsed.meta      || {};
    }

    console.log(`✅ ${questions.length} ta savol yuklandi`, meta);
    initTest();

  } catch (e) {
    console.error('Hash xatosi:', e);
    questions = DEMO;
    meta      = {};
    initTest();
  }
  showLoader(false);
}

function showLoader(on) {
  const el = document.getElementById('loader');
  if (el) el.style.display = on ? 'flex' : 'none';
}

function initTest() {
  if (!questions.length) {
    document.getElementById('qtxt').textContent = '❌ Savollar topilmadi!';
    return;
  }
  answers = new Array(questions.length).fill(null);
  score   = 0;
  current = 0;

  const SUBJ = { onatili:'📚 Ona tili', adabiyot:'📖 Adabiyot' };
  const DIFF = { easy:'🟢 Oson', medium:"🟡 O'rta", hard:'🔴 Qiyin' };
  const title = SUBJ[meta.subject] || '📚 Test';
  const sub   = meta.subcategory ? ` › ${meta.subcategory}` : '';
  const diff  = DIFF[meta.difficulty] || '';
  document.getElementById('hdr-title').textContent = title;
  const subEl = document.getElementById('hdr-sub');
  if (subEl) subEl.textContent = (meta.category || '') + sub + (diff ? ' · ' + diff : '');

  if (tg) {
    tg.setHeaderColor?.('#0f1523');
    tg.setBackgroundColor?.('#0f1523');
  }

  buildGrid();
  renderQuestion(0);
  document.getElementById('test-screen').style.display   = 'block';
  document.getElementById('result-screen').style.display = 'none';
}

function buildGrid() {
  const g = document.getElementById('grid');
  g.innerHTML = '';
  questions.forEach((_, i) => {
    const btn       = document.createElement('button');
    btn.className   = 'gbtn' + (i === 0 ? ' cur' : '');
    btn.id          = 'gb-' + i;
    btn.textContent = i + 1;
    btn.onclick     = () => jumpTo(i);
    g.appendChild(btn);
  });
}

function updateGrid() {
  questions.forEach((_, i) => {
    const btn = document.getElementById('gb-' + i);
    if (!btn) return;
    btn.className = 'gbtn';
    if      (i === current)            btn.classList.add('cur');
    else if (answers[i] === 'correct') btn.classList.add('ok');
    else if (answers[i] === 'wrong')   btn.classList.add('err');
    else if (answers[i] === 'skip')    btn.classList.add('skp');
  });
}

function jumpTo(i) {
  if (answers[i] !== null) return;
  current = i;
  renderQuestion(i);
}

function renderQuestion(i) {
  answered = false;
  const q     = questions[i];
  const total = questions.length;
  const qText = q.t || q.question_text || '';

  const pct = Math.round((i + 1) / total * 100);
  document.getElementById('prg-fill').style.width  = pct + '%';
  document.getElementById('prg-label').textContent = `${i + 1} / ${total}`;
  const pctEl = document.getElementById('prg-pct');
  if (pctEl) pctEl.textContent = pct + '%';
  document.getElementById('hdr-score').textContent = score + ' ball';

  document.getElementById('qnum').textContent = `SAVOL ${i + 1}`;
  document.getElementById('qtxt').textContent = qText;

  const imgEl  = document.getElementById('qimg');
  const imgSrc = q.img || '';
  imgEl.style.display = imgSrc ? 'block' : 'none';
  if (imgSrc) imgEl.src = imgSrc;

  const opts  = document.getElementById('opts');
  opts.innerHTML = '';
  const LBLS  = ['A', 'B', 'C', 'D'];
  const TEXTS = [q.a||'', q.b||'', q.c||'', q.d||''];

  LBLS.forEach((lbl, idx) => {
    const div = document.createElement('div');
    div.className = 'opt';
    div.id        = 'opt-' + lbl;
    div.innerHTML = `<span class="opt-ltr">${lbl}</span><span class="opt-txt">${TEXTS[idx]}</span>`;
    div.onclick   = () => selectOption(lbl);
    opts.appendChild(div);
  });

  const fb = document.getElementById('fb');
  fb.className     = 'fb';
  fb.style.display = 'none';
  fb.innerHTML     = '';

  document.getElementById('btn-skip').style.display = 'inline-flex';
  document.getElementById('btn-next').style.display = 'none';
  document.getElementById('btn-finish').style.display  = 'none';

  updateGrid();
}

function selectOption(label) {
  if (answered) return;
  answered = true;

  const q       = questions[current];
  const correct = q.ok || q.correct_answer || '';
  const isOk    = label === correct;

  document.querySelectorAll('.opt').forEach(o => {
    o.classList.add('off');
    o.onclick = null;
  });

  document.getElementById('opt-' + label).classList.add(isOk ? 'correct' : 'wrong');
  if (!isOk) document.getElementById('opt-' + correct)?.classList.add('hint');

  answers[current] = isOk ? 'correct' : 'wrong';
  if (isOk) score++;
  document.getElementById('hdr-score').textContent = score + ' ball';

  // Feedback + yechim linki
  const TEXTS       = { A: q.a, B: q.b, C: q.c, D: q.d };
  const fb          = document.getElementById('fb');
  const solutionUrl = meta.solution_url || '';
  const linkHtml    = solutionUrl
    ? `<br><a href="${solutionUrl}" target="_blank" style="color:inherit;opacity:0.85;font-size:12px;text-decoration:underline;">📹 Yechimni ko'rish</a>`
    : '';

  fb.style.display = 'flex';
  if (isOk) {
    fb.className = 'fb ok';
    fb.innerHTML = `✅ To'g'ri javob!${linkHtml}`;
  } else {
    fb.className = 'fb err';
    fb.innerHTML = `❌ Noto'g'ri! To'g'ri: <b>${correct}) ${TEXTS[correct] || ''}</b>${linkHtml}`;
  }

  document.getElementById('btn-skip').style.display = 'none';
  const isLast  = current === questions.length - 1;
  const allDone = answers.every(a => a !== null);
  if (allDone || isLast) {
    document.getElementById('btn-finish').style.display = 'inline-flex';
  } else {
    document.getElementById('btn-next').style.display = 'inline-flex';
  }

  updateGrid();
  tg?.HapticFeedback?.impactOccurred(isOk ? 'medium' : 'heavy');
}

function skipQuestion() {
  answers[current] = 'skip';
  updateGrid();
  const next = findNext(current + 1);
  if (next !== -1) { current = next; renderQuestion(current); }
  else showResult();
}

function nextQuestion() {
  const next = findNext(current + 1);
  if (next !== -1) { current = next; renderQuestion(current); }
  else showResult();
}

function findNext(from) {
  for (let i = from; i < questions.length; i++) {
    if (answers[i] === null) return i;
  }
  for (let i = 0; i < from; i++) {
    if (answers[i] === null) return i;
  }
  return -1;
}

function showResult() {
  const total   = questions.length;
  const correct = answers.filter(a => a === 'correct').length;
  const wrong   = answers.filter(a => a === 'wrong').length;
  const skip    = answers.filter(a => a === 'skip' || a === null).length;
  const pct     = total > 0 ? Math.round(correct / total * 100) : 0;

  document.getElementById('test-screen').style.display   = 'none';
  document.getElementById('result-screen').style.display = 'flex';

  const grades = [
    [90, '🏆', "A'lo (5)"],
    [70, '🎉', 'Yaxshi (4)'],
    [50, '📚', 'Qoniqarli (3)'],
    [0,  '😔', 'Qoniqarsiz (2)'],
  ];
  const [, emoji, grade] = grades.find(([min]) => pct >= min);

  document.getElementById('r-emoji').textContent   = emoji;
  document.getElementById('r-grade').textContent   = grade;
  document.getElementById('r-score').textContent   = pct + '%';
  document.getElementById('r-correct').textContent = correct;
  document.getElementById('r-wrong').textContent   = wrong;
  document.getElementById('r-skip').textContent    = skip;

  const rg = document.getElementById('result-grid');
  rg.innerHTML = '';
  const colMap = { correct:'ok', wrong:'err', skip:'skp' };
  answers.forEach((a, i) => {
    const d = document.createElement('div');
    d.className   = 'gbtn ' + (colMap[a] || '');
    d.textContent = i + 1;
    rg.appendChild(d);
  });

  if (tg) {
    tg.MainButton.setText('📤 Natijani yuborish');
    tg.MainButton.show();
    tg.MainButton.onClick(sendResult);
  }
  tg?.HapticFeedback?.notificationOccurred('success');
}

function sendResult() {
  const total   = questions.length;
  const correct = answers.filter(a => a === 'correct').length;
  const wrong   = answers.filter(a => a === 'wrong').length;
  const skip    = answers.filter(a => a === 'skip' || a === null).length;
  const pct     = total > 0 ? Math.round(correct / total * 100) : 0;

  const payload = JSON.stringify({
    correct,
    wrong,
    skip,
    total,
    score:          pct,
    subject:        meta.subject        || 'onatili',
    category:       meta.category       || 'aralash',
    subcategory:    meta.subcategory    || null,
    difficulty:     meta.difficulty     || null,
    is_attestation: meta.is_attestation || false,
  });

  if (tg) {
    tg.sendData(payload);
  } else {
    alert(`Natija: ${pct}% (${correct}/${total})`);
  }
}

window.skipQuestion = skipQuestion;
window.nextQuestion = nextQuestion;
window.showResult   = showResult;
window.sendResult   = sendResult;

loadQuestionsFromHash();
