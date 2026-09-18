"""Check exact approved content (canonical JSON) plus structural invariants."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = json.loads((ROOT / 'tests/content-sha256.json').read_text())
for name, expected in checks.items():
    value = json.loads((ROOT / name).read_text())
    actual = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert actual == expected, f'CONTENT MISMATCH {name}: expected {expected}, actual {actual}'
    print('Content unchanged:', name)
cases = json.loads((ROOT / 'data/cases.json').read_text())
missions = json.loads((ROOT / 'data/missions.json').read_text())
ref = json.loads((ROOT / 'data/reference.json').read_text())
words = json.loads((ROOT / 'data/words.json').read_text())
norm = lambda s: ''.join(c for c in s.lower() if c.isalnum())
assert len(cases) == len({c['code'] for c in cases}) == 20
assert len(missions) == 10 and len(words) == 25
assert [sum(c['game'] == g for c in cases) for g in [1, 2, 3]] == [5, 5, 10]
assert len({c['gwpage'] for c in cases}) == 19
for c in cases:
    assert c['letter'] == 'ABC'[c['game'] - 1]
    m = missions[c['key']]
    assert norm(m['name']) == norm(ref['matrix'][c['ownDispositionId']][c['opponentDispositionId']])
    assert norm(m['enemy']) == norm(ref['matrix'][c['opponentDispositionId']][c['ownDispositionId']])
    assert any(norm(w['name']) == norm(m['name']) for w in words)
    assert any(norm(w['name']) == norm(m['enemy']) for w in words)
    assert len(m['rounds']) == 5
    assert [r['battleRound'] for r in m['rounds']] == [1, 2, 3, 4, 5]
    for role in ['attacker', 'defender']:
        assert len(c['anchors'][role]) == 8
        for xy in c['anchors'][role].values():
            assert len(xy) == 2 and all(0 <= v <= 1 for v in xy)
    for kind in ['board', 'page']:
        f = ROOT / 'assets/layouts' / f'{kind}-{c["gwpage"]}.webp'
        assert f.is_file() and f.stat().st_size > 1000, f'Missing map: {f}'
assert sum(u['points'] for u in ref['units']) == 1995
assert sum(u['points'] for u in ref['units'] if u['player'] == 'Norman') == 955
assert sum(u['points'] for u in ref['units'] if u['player'] == 'Philipp') == 1040
print('PASS: exact content, 20 cases, 40 role maps, 10 five-round plans, 25 missions, 19 layouts and 1995 points.')

# Roster-revision invariants, independent of the content hashes.
assert ref['meta']['version'] == '1.1'
assert len(ref['formations']) == 13
assert len([u for u in ref['formations'] if u['player'] == 'Philipp']) == 4
assert sum(u['points'] for u in ref['formations']) == 1995
assert ref['deployment']['standardDrops'] == 10
assert 355 + 165 == ref['deployment']['bikePlusAllarusReservePoints'] > 500
u = {x['id']: x for x in ref['units']}
for i in [1, 2]:
    assert u[f'K{i}']['attachedTo'] == f'V{i}'
    assert u[f'V{i}']['ledBy'] == f'K{i}'
    assert '3 × Guardian Spear' in u[f'T{i}']['wargear']
    f = next(x for x in ref['formations'] if x['id'] == f'V{i}/K{i}')
    assert f['models'] == 4 and f['points'] == 355
for c in cases:
    assert c['rosterVersion'] == '1.1' and c['formation_note']
for m in missions.values():
    assert m['rosterVersion'] == '1.1'
    assert all(r['norman'] and r['philipp'] for r in m['rounds'])
active_text = (ROOT/'app.mjs').read_text() + json.dumps(missions,ensure_ascii=False) + (ROOT/'data/chapters.json').read_text()
for obsolete in ['K1 und K2 starten einzeln', 'Beide Captains zunächst separat', 'K2 bleibt separat', 'K1 an V1 anschließen', '15 eigenständige Einheiten', '12 Aufstellvorgänge', 'mit Vexilla 9 OC', 'zunächst separater Captain']:
    assert obsolete not in active_text, obsolete
assert "dropzone:2026-10-10:v1:" in (ROOT/'core.mjs').read_text()
print('PASS: attached Captains, four Custodes formations, 10 drops, three spears per Allarus squad, unchanged note namespace.')
