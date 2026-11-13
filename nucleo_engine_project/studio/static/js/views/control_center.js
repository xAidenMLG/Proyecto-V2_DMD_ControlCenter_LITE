// Vista GUIDED (Control Center) — Fase 3 (spec v1.4, §7.3).
// Capa de interacción, NO un motor musical: convierte elecciones humanas
// sencillas en una intención válida y delega TODA la resolución en el
// Intérprete Universal (F2) vía el backend real (jobs → runner_cc).
// Reglas §7: exactamente 6 controles + identidad + protagonista; vacío =
// auto (la UI nunca rellena por el intérprete); cero parámetros técnicos
// (sin BPM, tonalidad, gain ni seed — C-08).
import { state, emit } from '../state.js';
import { el, $, toast, toastErr, toastOk, fmtBytes, fmtDur, copyText, download } from '../ui.js';
import { API } from '../api.js';

let pollTimer = null;
let catalogo = null;
let sel = null;          // selecciones actuales de la vista
let lastGen = null;      // gen_id del último trabajo guiado terminado

const LS_KEY = (pid) => 'dmd.guided.' + pid;

export async function render(host) {
  host.innerHTML = '';
  stopPoll();
  host.append(
    el('h1', {}, 'Guided'),
    el('p', { class: 'sub' },
      'Describe la canción con decisiones humanas y el Intérprete Universal resuelve las ~40 decisiones técnicas. Lo que dejes en «Automático» lo decide el intérprete y queda registrado en el plan.'));

  try {
    catalogo = await API.guidedCatalog();
  } catch (e) {
    host.append(el('div', { class: 'empty' }, 'No se pudo cargar el catálogo: ' + (e.error || e)));
    return;
  }

  // restaurar selecciones de este proyecto (repetir sin reconstruir, §7)
  sel = loadSel();
  lastGen = null;

  host.append(bloqueIdentidad(), bloqueControles(), bloqueEjecucion(), bloqueHistorial());

  refreshResumen();
  try {
    const jobs = await API.jobs(state.project.id);
    const prev = jobs.find(j => j.spec_resumen && j.spec_resumen.guided);
    if (prev) showJob(prev.jid, { silent: true });
  } catch { /* primera visita */ }
  paintHistorial();
}

/* ------------------------------------------------------------- identidad */
function bloqueIdentidad() {
  const estilos = catalogo.estilos, acces = catalogo.accesibilidades,
        protas = catalogo.protagonistas;
  const selEstilo = selectFld('Estilo musical', estilos, sel.identity.style,
    v => { sel.identity.style = v; persist(); });
  const selAcc = selectFld('Carácter de la melodía', acces, sel.identity.accessibility,
    v => { sel.identity.accessibility = v; persist(); });
  const selProta = selectFld('Protagonista', protas, sel.identity.protagonist,
    v => { sel.identity.protagonist = v; persist(); });
  const titulo = el('input', { type: 'text', maxLength: 60,
    placeholder: 'Vacío = el intérprete le pone nombre' });
  titulo.value = sel.title || '';
  titulo.addEventListener('input', () => { sel.title = titulo.value.trim() || null; persist(); });
  return el('div', { class: 'card' },
    el('h2', {}, 'Identidad de la canción'),
    el('div', { class: 'grid-2' },
      el('div', { class: 'grid-2' }, selEstilo, selAcc),
      selProta),
    el('label', { class: 'fld', style: 'margin-top:12px' },
      el('span', { class: 'lbl' }, 'Título (opcional)'), titulo));
}

/* ---------------------------------------------------------- 6 controles */
function bloqueControles() {
  const grid = el('div', { class: 'grid-3' });
  for (const c of catalogo.controles) {
    const opciones = [{ v: '', label: 'Automático — lo decide el intérprete' }]
      .concat(c.opciones.map(o => ({ v: o.id, label: o.label })));
    const s = el('select', {}, opciones.map(o =>
      el('option', { value: o.v, selected: (sel.controls[c.id] || '') === o.v }, o.label)));
    s.addEventListener('change', () => {
      sel.controls[c.id] = s.value || null;
      persist(); refreshResumen();
    });
    grid.append(el('div', { class: 'mode-card', style: 'cursor:default' },
      el('h3', {}, c.pregunta),
      s));
  }
  return el('div', { class: 'card' },
    el('h2', {}, 'Los seis controles'),
    el('p', { class: 'tiny', style: 'margin:0 0 12px' },
      'Todo lo que dejes en Automático lo resuelve el intérprete según la identidad elegida.'),
    grid);
}

function selectFld(label, opciones, valor, onchange) {
  const s = el('select', {}, opciones.map(o =>
    el('option', { value: o.id, selected: valor === o.id }, o.label)));
  s.addEventListener('change', () => onchange(s.value));
  return el('label', { class: 'fld' }, el('span', { class: 'lbl' }, label), s);
}

/* ------------------------------------------------------------- resumen */
function resumenIntencion() {
  const parts = [];
  const estilo = catalogo.estilos.find(e => e.id === sel.identity.style);
  const acc = catalogo.accesibilidades.find(a => a.id === sel.identity.accessibility);
  const prota = catalogo.protagonistas.find(p => p.id === sel.identity.protagonist);
  if (estilo) parts.push(estilo.label.split('—')[0].trim());
  if (acc) parts.push(acc.label.split('—')[0].trim());
  if (prota) parts.push('protagoniza ' + prota.label.split('—')[0].trim());
  for (const c of catalogo.controles) {
    const v = sel.controls[c.id];
    if (!v) continue;
    const op = c.opciones.find(o => o.id === v);
    if (op) parts.push(op.label.split('—')[0].trim().toLowerCase());
  }
  return parts.join(' · ') || 'todo automático';
}

function refreshResumen() {
  const n = $('#g-resumen');
  if (n) n.textContent = resumenIntencion();
}

/* ----------------------------------------------------------- ejecución */
function bloqueEjecucion() {
  const wav = el('input', { type: 'checkbox', id: 'g-wav', checked: !!sel.wav });
  wav.addEventListener('change', () => { sel.wav = wav.checked; persist(); });
  const btn = el('button', { class: 'btn primary', id: 'g-gen', onclick: () => generar(btn) },
    '✦ Generar canción');
  const cancel = el('button', { class: 'btn danger', id: 'g-cancel', hidden: true,
    onclick: () => doCancel() }, '✕ Cancelar');
  const status = el('span', { id: 'g-status', class: 'mono tiny muted' }, 'sin ejecución en curso');
  const bar = el('div', { class: 'progress-track', style: 'margin-top:12px' },
    el('div', { class: 'progress-bar', id: 'g-bar' }));
  const resultado = el('div', { id: 'g-resultado' });
  const logTerm = el('div', { class: 'term', id: 'g-log' }, 'Sin actividad todavía.');
  return el('div', { class: 'card' },
    el('h2', {}, 'Generar'),
    el('p', { class: 'tiny', style: 'margin:0 0 10px' }, 'Así se leerá tu intención:'),
    el('div', { class: 'mono', id: 'g-resumen', style: 'color:var(--acc); margin-bottom:14px' }, ''),
    el('div', { class: 'row' }, btn, cancel, el('span', { class: 'right' }), status),
    el('div', { class: 'row', style: 'margin-top:10px; gap:8px' },
      wav, el('span', { class: 'tiny' }, 'Renderizar también WAV (requiere FluidSynth)')),
    bar, resultado,
    el('details', { class: 'adv', style: 'margin-top:14px' },
      el('summary', {}, 'Registro técnico de la ejecución'),
      logTerm));
}

async function generar(btn) {
  btn.disabled = true;
  paintResultado(null);
  try {
    const body = {
      identity: { ...sel.identity },
      controls: Object.fromEntries(Object.entries(sel.controls).filter(([, v]) => v)),
      title: sel.title || undefined,
      wav: !!sel.wav,
    };
    const job = await API.guidedGenerate(state.project.id, body);
    state.lastJob = job.jid;
    showJob(job.jid);
  } catch (e) {
    btn.disabled = false;
    const log = $('#g-log');
    log.innerHTML = '';
    log.append(el('div', { class: 't-err' }, (e && e.error) || String(e)));
    if (e && e.fase === 'intención inválida') {
      toast('Revisa tus elecciones: ' + ((e.error || '').slice(0, 120)), 'err', 6500);
      paintResultado(el('div', { class: 'err-text' },
        'La combinación elegida no es válida para el intérprete: ' + (e.error || '')));
    } else {
      toastErr(e);
    }
  }
}

function showJob(jid, { silent = false } = {}) {
  $('#g-cancel').hidden = false;
  $('#g-status').textContent = 'consultando…';
  pollJob(jid, silent);
}

function pollJob(jid, silent = false) {
  stopPoll();
  const tick = async () => {
    let j;
    try { j = await API.job(jid); }
    catch { stopPoll(); return; }
    paintJob(j);
    if (['running', 'queued'].includes(j.state)) {
      pollTimer = setTimeout(tick, 700);
    } else {
      stopPoll();
      $('#g-cancel').hidden = true;
      $('#g-gen').disabled = false;
      if (j.state === 'done' && !silent) toastOk('Canción lista: ' +
        ((j.result?.plan?.title) || 'ver abajo'));
      if (j.state === 'done') { lastGen = j.gen_id; paintHistorial(); }
      else if (j.state === 'error' && !silent) {
        paintResultado(el('div', { class: 'err-text' },
          'La producción falló: ' + (j.result?.error || 'motivo desconocido') +
          ' — el registro técnico tiene el detalle.'));
      }
    }
  };
  tick();
}

function paintJob(j) {
  const log = $('#g-log');
  log.innerHTML = '';
  for (const line of (j.log_tail || [])) {
    log.append(el('div', {
      class: line.startsWith('## ') ? 't-step' :
        (line.includes('Traceback') || line.includes('Error') ? 't-err' : '')
    }, line || ' '));
  }
  log.scrollTop = log.scrollHeight;
  $('#g-status').textContent =
    { running: 'produciendo…', queued: 'en cola…', done: 'completado',
      error: 'error', cancelled: 'cancelada', interrupted: 'interrumpida' }[j.state] || j.state;
  const bar = $('#g-bar');
  if (j.state === 'running') bar.className = 'progress-bar indet';
  else { bar.className = 'progress-bar'; bar.style.width = j.state === 'done' ? '100%' : '0%'; }
  if (j.state === 'done') paintResultado(tarjetaResultado(j));
  if (j.state === 'error') {
    $('#g-status').innerHTML =
      `<span style="color:var(--err)">error: ${escapeH(j.result?.error || '')}</span>`;
  }
}

function tarjetaResultado(j) {
  const p = j.result?.plan || {};
  const prod = j.result?.produccion || {};
  const cc = j.result?.capa_c;
  const fila = (k, v) => el('div', { style: 'margin-bottom:4px' },
    el('span', { class: 'lbl', style: 'margin-bottom:1px' }, k),
    el('span', {}, v == null || v === '' ? '—' : String(v)));
  const caja = el('div', { class: 'grid-2' },
    el('div', {},
      fila('Título', p.title),
      fila('Seed (persistida en el plan)', p.seed),
      fila('Tempo', p.bpm ? p.bpm + ' BPM' : null),
      fila('Forma', p.template),
      fila('Perfil de producción', p.profile)),
    el('div', {},
      fila('Duración real', fmtDur(prod.duracion_s)),
      fila('Compases', prod.compases ?? p.bars_total),
      fila('Decisiones resueltas por el intérprete', p.decisiones_resueltas),
      fila('Capa C (verificación estructural)',
        cc ? (cc.ok ? 'OK' + (cc.gates_ok?.length ? ` · ${cc.gates_ok.length} gates` : '')
                  : 'FALLA: ' + (cc.fallidos || []).join(', ')) : 'no aplicada')));
  const shaRow = el('div', { class: 'row', style: 'margin-top:10px' },
    el('span', { class: 'mono tiny muted' }, 'sha256 ' + (prod.sha256 || '').slice(0, 24) + '…'),
    el('button', { class: 'btn icon ghost', title: 'copiar sha256',
      onclick: () => copyText(prod.sha256 || '') }, '⧉'),
    el('a', { class: 'btn sm ghost', href: '#/results' }, 'Abrir en Results'));
  const cajaErr = cc && !cc.ok ? el('div', { class: 'err-text' },
    'La capa C detectó problemas estructurales: ' + (cc.fallidos || []).join(', ')) : null;
  return el('div', { class: 'sec-item open', style: 'margin-top:14px; padding:14px' },
    el('h2', {}, 'Tu canción está lista'),
    caja, shaRow, cajaErr, zonaEscuchaYDescargas());
}

function zonaEscuchaYDescargas() {
  const audioBox = el('div', { style: 'margin-top:12px' });
  const dlBox = el('div', { class: 'row', style: 'margin-top:10px' });
  const pid = state.project.id, gid = lastGen;
  if (!gid) return el('div', { class: 'tiny muted', style: 'margin-top:10px' },
    'Artefactos en Results.');
  API.generation(pid, gid).then(g => {
    for (const [key, meta] of Object.entries(g.archivos || {})) {
      if (!key.includes('/')) continue;
      const slash = key.indexOf('/');
      const folder = key.slice(0, slash), fname = key.slice(slash + 1);
      const url = API.audioUrl(pid, gid, folder, fname);
      if (/\.(wav|mp3)$/.test(fname) && meta && meta.bytes) {
        audioBox.append(el('div', {},
          el('span', { class: 'lbl' }, 'Escucha (' + fname + ' · ' + fmtBytes(meta.bytes) + ')'),
          el('audio', { controls: true, src: url, preload: 'none' })));
      }
      if (/\.(mid|wav|mp3)$/.test(fname)) {
        dlBox.append(el('button', { class: 'btn sm ghost',
          onclick: () => download(url, fname) }, '↓ ' + fname));
      }
    }
    for (const f of ['plan.json', 'doc.json', 'capa_c.json', 'events.json']) {
      const key = Object.keys(g.archivos || {}).find(k => k.endsWith('/' + f));
      if (key) {
        const folder = key.slice(0, key.indexOf('/'));
        dlBox.append(el('button', { class: 'btn sm ghost',
          onclick: () => download(API.audioUrl(pid, gid, folder, f), f) }, '↓ ' + f));
      }
    }
    if (!dlBox.children.length) dlBox.append(el('span', { class: 'tiny' },
      'artefactos no encontrados'));
  }).catch(e => dlBox.append(el('span', { class: 'err-text' }, String(e.error || e))));
  return el('div', {}, audioBox, dlBox);
}

function paintResultado(nodo) {
  const r = $('#g-resultado');
  if (r) r.innerHTML = '';
  if (nodo && r) r.append(nodo);
}

async function doCancel() {
  const jid = state.lastJob;
  if (!jid) return;
  try {
    await API.cancelJob(jid);
    toast('Cancelando…', 'info', 2500);
  } catch (e) { toastErr(e); }
}

/* ------------------------------------------------------------ historial */
function bloqueHistorial() {
  return el('div', { class: 'card' },
    el('h2', {}, 'Canciones guiadas de este proyecto'),
    el('div', { id: 'g-historial' }, el('div', { class: 'tiny muted' }, 'cargando…')));
}

async function paintHistorial() {
  const host = $('#g-historial');
  if (!host) return;
  let jobs = [];
  try { jobs = await API.jobs(state.project.id); } catch { }
  const guiadas = jobs.filter(j => j.spec_resumen && j.spec_resumen.guided);
  host.innerHTML = '';
  if (!guiadas.length) {
    host.append(el('div', { class: 'tiny muted' },
      'Todavía no hay generaciones guiadas en este proyecto.'));
    return;
  }
  for (const j of guiadas.slice(0, 12)) {
    const p = j.result?.plan;
    const estado = { done: ['ok', 'badge ok'], error: ['error', 'badge err'],
      running: ['produciendo…', 'badge acc'], cancelled: ['cancelada', 'badge warn'],
      interrupted: ['interrumpida', 'badge warn'], queued: ['en cola', 'badge acc'] }[j.state] ||
      [j.state, 'badge'];
    host.append(el('div', { class: 'spread', style: 'padding:7px 0; border-bottom:1px solid var(--line)' },
      el('div', { class: 'row', style: 'gap:10px' },
        el('span', { class: estado[1] }, estado[0]),
        el('b', {}, p?.title || j.spec_resumen.identity || j.jid),
        el('span', { class: 'mono tiny muted' },
          (p ? `seed ${p.seed}` : '') + (p ? ' · ' : '') + (p?.template || '')),
        el('span', { class: 'mono tiny muted' }, j.gen_id || '')),
      el('div', { class: 'row', style: 'gap:8px' },
        el('span', { class: 'mono tiny muted' },
          j.state === 'done' ? fmtDur(j.result?.produccion?.duracion_s) : ''),
        el('a', { class: 'btn sm ghost', href: '#/results' }, 'Results'))));
  }
}

/* ------------------------------------------------------- persistencia UI */
function loadSel() {
  let base = {
    identity: { style: 'dark_triphop', accessibility: 'balanced', protagonist: 'sax_tenor' },
    controls: {}, title: null, wav: false,
  };
  try {
    const raw = localStorage.getItem(LS_KEY(state.project.id));
    if (raw) base = { ...base, ...JSON.parse(raw) };
  } catch { }
  base.controls = base.controls || {};
  base.identity = base.identity || {};
  return base;
}

function persist() {
  try { localStorage.setItem(LS_KEY(state.project.id), JSON.stringify(sel)); } catch { }
}

function escapeH(s) {
  return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

function stopPoll() { if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; } }
