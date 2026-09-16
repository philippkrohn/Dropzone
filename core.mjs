export const VIEWS = ['table', 'plan', 'rules', 'missions', 'notes'];
export const ROLES = ['attacker', 'defender'];
export const TURNS = ['unknown', 'first', 'second'];
export const STORAGE = 'dropzone:2026-10-10:v1:';
export function resolveCase(cases, state) {
  const own = state.game === 1 ? 'reconnaissance' : state.game === 2 ? 'priority-assets' : state.own;
  return cases.find(c => c.game === state.game && c.ownDispositionId === own && c.opponentDispositionId === state.opp) ?? null;
}
export function parseSelection(search, cases) {
  const p = new URLSearchParams(search);
  const state = {game: 1, own: '', opp: '', role: 'defender', turn: 'unknown', view: 'table', error: ''};
  const fail = message => { state.error = message; };
  if (p.has('case')) {
    const c = cases.find(c => c.code === p.get('case'));
    if (!c) fail('Dieser Szenariocode ist nicht vorhanden. Bitte wähle das Spiel und die Dispositionen neu.');
    else Object.assign(state, {game: c.game, own: c.ownDispositionId, opp: c.opponentDispositionId});
  } else {
    if (p.has('game')) { const n = Number(p.get('game')); if ([1,2,3].includes(n)) state.game = n; else fail('Die Spielnummer muss 1, 2 oder 3 sein.'); }
    if (p.has('own')) state.own = p.get('own');
    if (p.has('opp')) state.opp = p.get('opp');
    if (state.opp && !cases.some(c => c.opponentDispositionId === state.opp)) { state.opp = ''; fail('Unbekannte gegnerische Disposition.'); }
    if (state.game === 3 && state.own && !['reconnaissance','priority-assets'].includes(state.own)) { state.own = ''; fail('Euch kann nur Reconnaissance oder Priority Assets zugewiesen werden.'); }
  }
  for (const [key, values] of [['role',ROLES],['turn',TURNS],['view',VIEWS]]) {
    if (p.has(key)) { if (values.includes(p.get(key))) state[key] = p.get(key); else fail(`Ungültige Auswahl: ${key}. Bitte neu auswählen.`); }
  }
  return state;
}
export function selectionQuery(state, c) {
  const p = new URLSearchParams();
  if (c) p.set('case',c.code);
  else { p.set('game',String(state.game)); if (state.game===3 && state.own) p.set('own',state.own); if(state.opp) p.set('opp',state.opp); }
  p.set('role',state.role); p.set('turn',state.turn); p.set('view',state.view);
  return `?${p}`;
}
export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
export function validateNotesFile(value) {
  if (!value || value.app !== 'Dropzone' || value.version !== 1 || !Array.isArray(value.records) || value.records.length > 60) throw new Error('Keine gültige Dropzone-Notizdatei.');
  for (const r of value.records) {
    if (!r || !/^dropzone:2026-10-10:v1:game[123]:[ABC]\d{2}$/.test(r.key) || !r.value || typeof r.value !== 'object' || Array.isArray(r.value)) throw new Error('Ungültiger Notizschlüssel.');
    for (const [k,v] of Object.entries(r.value)) {
      if (!/^(opponent|warlord|cpP|cpN|note[0-4]|resource\d{1,2}|check[0-5]|score[0-5]-[0-3])$/.test(k) || !['string','boolean'].includes(typeof v) || (typeof v === 'string' && v.length > 4000)) throw new Error('Unzulässiger Notizinhalt.');
    }
  }
  return value.records;
}
