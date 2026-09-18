from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'BEDIENUNG.md';s=p.read_text().replace('Die acht Nummern erklären 12 Aufstellvorgänge der empfohlenen Standardformation; B2/T2 sind in dieser Empfehlung in Reserve, S1 im Rhino. Captains starten separat.','Die acht Nummern erklären zehn Aufstellvorgänge der empfohlenen Standardformation; B2/T2 sind in Reserve, S1 im Rhino. K1 führt V1 und K2 führt V2 ab Spielbeginn: Anker 7/8 stehen jeweils für eine Vierer-Einheit mit 355 Punkten. T1/T2 tragen je drei Guardian Spears ohne Vexilla.').replace('Taktischer Stand: **16.09.2026 / Dossier v1.0**. Keine stille Regelaktualisierung oder neue taktische Bewertung.','Taktischer Stand: **18.09.2026 / Web v1.1**, angepasst an Philipps neue Custodes-Liste. Regel- und Missionsbasis weiterhin 16.09.2026; keine allgemeine Regelaktualisierung. Das ursprüngliche PDF bleibt unverändert auf v1.0.').replace('Team-Warlord noch offen, K1 nur Empfehlung.','K1 ist Warlord laut neuem Custodes-Export; die Team-Warlord-Festlegung mit Norman abgleichen.').replace('zehn unveränderte Missionspläne','zehn auf die neue Formation angepasste Missionspläne').replace('neun unveränderte Vorbereitungskapitel','neun aktualisierte Vorbereitungskapitel').replace('Für die Webfassung wurde nur die technische Struktur angepasst.','v1.1 ändert ausdrücklich die vom Listenwechsel betroffenen Strategien und Formationen. Missionswortlaute, Wertungsbedingungen und Punktegrenzen bleiben unverändert.').replace('Bei Verbindung unten „Offlinepaket speichern“ wählen','Nach dem Listenupdate die Seite bei bestehender Verbindung neu laden. Unten „Offlinepaket speichern / aktualisieren“ wählen')
s+='\n## Listenrevision v1.1\n\nBeide Captains sind Start-Leader; für den Startanschluss keine CP einplanen. Eine Bike-Formation (355) plus Allarus (165) wären 520 Punkte Reserve und überschreiten die 500-Punkte-Spielergrenze. Priorität: Philipp entfernt wertungsrelevante Gegner, Norman stellt Aktionshelfer und Halter. Custodes übernehmen erforderliche Missionsarbeit, wenn nur sie die entscheidenden Punkte erreichen können.\n\nLokale Notizschlüssel und Ressourcen-Reihenfolge sind unverändert. Beim Service-Worker-Update werden nur unveränderte Karten übernommen, keine alten Regeln oder Strategiedaten. Bestehende eigene Notizen auf überholte Solo-Captain-Pläne prüfen; die Website löscht sie nicht.\n\nRollback-Ausgang für diese Revision: `ebb70f4320c295ecd4821d65c2692b73b68d8733`. Eine Rücknahme als neuen Commit veröffentlichen und dabei die Offline-Cache-Version erneut erhöhen.\n'
p.write_text(s)
p=R/'tests/browser_smoke.py';s=p.read_text().replace('import argparse','import argparse\nimport os').replace('browser = p.chromium.launch()','browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))').replace("page.pdf(path=str(OUT / 'print-sample.pdf'), format='A4', print_background=True)","# No PDF is regenerated for the website-only roster revision.")
s=s.replace("expect(page.locator('.mission-header h2')).to_have_text(missions[c['key']]['name'])","expect(page.locator('.mission-header h2')).to_have_text(missions[c['key']]['name'])\n                expect(page.locator('#roster-update')).to_contain_text('Web v1.1')\n                expect(page.locator('.legend-description')).to_contain_text('angeschlossene Vierer-Bike-Einheit')\n                assert 'K1 und K2 starten einzeln' not in page.locator('#app').inner_text()")
s=s.replace("goto('?game=3&opp=disruption')","goto('?case=A01&view=rules')\n        assert page.locator('.unit-card.philipp').count() == 4\n        expect(page.locator('.unit-card.philipp').nth(2)).to_contain_text('355 Punkte')\n        expect(page.locator('.unit-card.philipp').first).to_contain_text('3 × Guardian Spear')\n        goto('?game=3&opp=disruption')")
p.write_text(s)
p=R/'tests/live_smoke.py';s=p.read_text().replace("'data/words.json']","'data/words.json', 'data/custodes-roster-2026-09-18.txt']").replace("expect(page.locator('#app')).to_have_attribute('data-case', code)","expect(page.locator('#app')).to_have_attribute('data-case', code)\n        expect(page.locator('#roster-update')).to_contain_text('Web v1.1')\n        assert 'K1 und K2 starten einzeln' not in page.locator('#app').inner_text()")
p.write_text(s)
p=R/'tests/verify_content.py';s=p.read_text();s+='''
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
''';p.write_text(s)
print('Docs and roster-specific regression checks prepared.')
