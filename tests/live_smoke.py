"""Verify the public GitHub Pages deployment, not merely the repository."""
import hashlib
import json
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://philippkrohn.github.io/Dropzone/'
OUT = ROOT / 'qa-live'
OUT.mkdir(exist_ok=True)
report = {'url': BASE, 'files': [], 'scenarios': [], 'errors': []}
files = ['index.html', 'app.mjs', 'core.mjs', 'style.css', 'sw.js', 'data/cases.json', 'data/missions.json', 'data/reference.json', 'data/chapters.json', 'data/words.json', 'data/custodes-roster-2026-09-18.txt']
for attempt in range(12):
    try:
        report['files'] = []
        for name in files:
            request = urllib.request.Request(BASE + name, headers={'User-Agent':'Dropzone-Deployment-Check/1.0', 'Cache-Control':'no-cache'})
            with urllib.request.urlopen(request, timeout=30) as r:
                remote = r.read()
                assert r.status == 200
            expected = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            assert hashlib.sha256(remote).hexdigest() == expected, 'Publication not current: ' + name
            report['files'].append({'name':name,'sha256':expected})
        break
    except Exception:
        if attempt == 11:
            raise
        time.sleep(10)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
    page.on('pageerror', lambda e: report['errors'].append(str(e)))
    for code in ['A01','B02','C08']:
        r = page.goto(BASE + '?case=' + code + '&role=defender&turn=first', wait_until='domcontentloaded')
        assert r.ok
        expect(page.locator('#app')).to_have_attribute('data-case', code)
        expect(page.locator('#roster-update')).to_contain_text('Web v1.1')
        assert 'K1 und K2 starten einzeln' not in page.locator('#app').inner_text()
        page.locator('#app .map img').scroll_into_view_if_needed()
        page.locator('#app .map img').evaluate('(i)=>i.decode()')
        assert page.locator('#app .marker').count() == 8
        page.select_option('#role-choice','attacker')
        assert page.input_value('#turn-choice') == 'first'
        page.locator('.main-nav [data-view="plan"]').click()
        assert page.locator('#app .round-card').count() == 5
        report['scenarios'].append(code)
    page.goto(BASE + '?case=A01&role=defender&turn=first', wait_until='networkidle')
    page.screenshot(path=str(OUT / 'live-desktop.png'), full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(OUT / 'live-mobile.png'), full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not report['errors'], report['errors']
    report['passed'] = True
    (OUT / 'live-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    browser.close()
