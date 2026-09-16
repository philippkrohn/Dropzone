"""Real-browser functional checks. Run against a local HTTP server or Pages."""
import argparse
import json
import sys
import traceback
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://127.0.0.1:8765/Dropzone/')
args = parser.parse_args()
OUT = ROOT / 'qa-artifacts'
OUT.mkdir(exist_ok=True)
cases = json.loads((ROOT / 'data/cases.json').read_text())
missions = json.loads((ROOT / 'data/missions.json').read_text())
report = {'base': args.base, 'checks': [], 'errors': []}
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    page = context.new_page()
    page.on('pageerror', lambda e: report['errors'].append(str(e)))
    def goto(query):
        response = page.goto(args.base + query, wait_until='domcontentloaded')
        assert response.ok, response.status
        page.wait_for_selector('#opponent-choice')
    try:
        for c in cases:
            for role in ['attacker', 'defender']:
                goto(f'?case={c["code"]}&role={role}&turn=unknown')
                expect(page.locator('#app')).to_have_attribute('data-case', c['code'])
                expect(page.locator('.mission-header h2')).to_have_text(missions[c['key']]['name'])
                img = page.locator('#app .map img')
                img.scroll_into_view_if_needed()
                img.evaluate('(i)=>i.decode()')
                assert img.evaluate('(i)=>i.naturalWidth') > 900
                assert page.locator('#app .marker').count() == 8
                for number, xy in c['anchors'][role].items():
                    pos = page.locator(f'#app .marker[data-anchor="{number}"]').evaluate('(e)=>[parseFloat(e.style.left)/100,parseFloat(e.style.top)/100]')
                    assert all(abs(pos[i]-xy[i]) < 1e-8 for i in [0,1])
                assert page.locator('.turn-box').count() == 2
                for turn in ['first', 'second']:
                    page.select_option('#turn-choice', turn)
                    assert page.input_value('#role-choice') == role
                    assert page.locator('.turn-box').count() == 1
                report['checks'].append(c['code'] + ' ' + role + ': map, 8 anchors, independent turn order')
            page.locator('.main-nav [data-view="plan"]').click()
            assert page.locator('#app .round-card').count() == 5
            for r in missions[c['key']]['rounds']:
                text = page.locator('[data-round="' + str(r['battleRound']) + '"]').inner_text()
                assert r['norman'] in text and r['philipp'] in text
        goto('?game=3&opp=disruption')
        assert page.get_attribute('#app', 'data-case') == ''
        assert page.input_value('#own-choice') == ''
        page.select_option('#own-choice', 'priority-assets')
        assert page.get_attribute('#app', 'data-case') == 'C08'
        goto('?case=NOPE')
        assert page.get_attribute('#app', 'data-case') == ''
        assert page.locator('#app [role="alert"]').count() == 1
        goto('?case=A01&role=defender&turn=first')
        page.locator('[data-action="zoom"]').click()
        expect(page.locator('#modal')).to_be_visible()
        page.locator('#map-zoom').evaluate("e=>{e.value='200';e.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert page.locator('#zoom-canvas').evaluate('(e)=>e.style.width') == '200%'
        page.keyboard.press('Escape')
        page.locator('[data-action="original"]').click()
        page.locator('#zoom-canvas img').evaluate('(i)=>i.decode()')
        page.keyboard.press('Escape')
        page.locator('.main-nav [data-view="missions"]').click()
        assert page.locator('.matrix button').count() == 25
        for i in range(25):
            page.locator('.matrix button').nth(i).click()
            assert 'PRIMARY MISSION' in page.locator('#modal .word').inner_text()
            page.keyboard.press('Escape')
        page.fill('#mission-search', 'sensor sweep')
        assert page.locator('.word-entry:not([hidden])').count() == 2
        page.fill('#mission-search', 'zzzxzzzz')
        assert page.locator('.word-entry:not([hidden])').count() == 0
        goto('?case=C08&view=notes')
        page.fill('#note-opponent', 'Browser-Test')
        page.fill('#note-cpP', '2')
        page.fill('#note-cpN', '4')
        page.fill('#note-field-0', 'PRIVATE <script>not executed</script>')
        page.locator('[data-note="resource0"]').check()
        page.locator('[data-note="score0-0"]').fill('7')
        page.locator('[data-note="score5-0"]').fill('5')
        expect(page.locator('[data-total="0"]')).to_have_text('12')
        page.reload()
        expect(page.locator('#note-opponent')).to_have_value('Browser-Test')
        expect(page.locator('#note-field-0')).to_have_value('PRIVATE <script>not executed</script>')
        expect(page.locator('[data-note="resource0"]')).to_be_checked()
        goto('?case=C09&view=notes')
        expect(page.locator('#note-opponent')).to_have_value('')
        goto('?case=C08&view=notes')
        with page.expect_download() as d:
            page.locator('[data-action="export"]').click()
        d.value.save_as(OUT / 'notes-export-test.json')
        exported = json.loads((OUT / 'notes-export-test.json').read_text())
        assert exported['app'] == 'Dropzone' and len(exported['records']) == 1
        page.once('dialog', lambda d: d.dismiss())
        page.locator('[data-action="reset"]').click()
        expect(page.locator('#note-opponent')).to_have_value('Browser-Test')
        assert 'PRIVATE' not in page.url
        report['checks'].append('Matrix 25, search, game-three assignment, invalid link, zoom, local note isolation/persistence/export and cancel-safe reset')
        for width in [320, 390, 768, 1440]:
            page.set_viewport_size({'width': width, 'height': 900})
            for view in ['table', 'plan', 'rules', 'missions', 'notes']:
                goto('?case=A01&role=defender&view=' + view)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width,view)
            report['checks'].append(f'{width}px: no page-level horizontal overflow across all five views')
        goto('?case=A01&role=defender&turn=first')
        page.screenshot(path=str(OUT / 'desktop.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(OUT / 'mobile.png'), full_page=True)
        page.locator('#theme').click()
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        page.screenshot(path=str(OUT / 'mobile-light.png'), full_page=True)
        page.evaluate('window.print=()=>window.__printed=true')
        page.locator('[data-action="print"]').click()
        page.wait_for_function('window.__printed===true')
        assert page.locator('#print-area .round-card').count() == 5
        page.emulate_media(media='print')
        page.pdf(path=str(OUT / 'print-sample.pdf'), format='A4', print_background=True)
        page.emulate_media(media='screen')
        page.locator('#offline').click()
        expect(page.locator('#offline-status')).to_contain_text('Offlinepaket gespeichert', timeout=90000)
        context.set_offline(True)
        goto('?case=C10&role=attacker&view=table')
        expect(page.locator('#app')).to_have_attribute('data-case', 'C10')
        page.locator('#app .map img').evaluate('(i)=>i.decode()')
        page.locator('.main-nav [data-view="rules"]').click()
        assert page.locator('#app details.chapter').count() == 9
        report['checks'].append('Print document includes complete five-round plan; full offline reload includes previously unopened C10 and all chapters')
        context.set_offline(False)
        assert not report['errors'], report['errors']
        report['passed'] = True
    except Exception as e:
        report['passed'] = False
        report['failure'] = str(e)
        report['url'] = page.url
        try:
            page.screenshot(path=str(OUT / 'failure.png'), full_page=True)
            (OUT / 'failure.html').write_text(page.content())
        except Exception:
            pass
        raise
    finally:
        (OUT / 'browser-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        browser.close()
