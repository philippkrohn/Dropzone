"""Exercise a real v1.0 -> v1.1 upgrade at one origin without touching user data."""
from pathlib import Path
import functools,http.server,json,shutil,subprocess,tempfile,threading
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa-artifacts';OUT.mkdir(exist_ok=True)
BASE_COMMIT='ebb70f4320c295ecd4821d65c2692b73b68d8733'
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);site=root/'Dropzone';site.mkdir()
 archive=subprocess.run(['git','archive','--format=tar',BASE_COMMIT],cwd=ROOT,check=True,capture_output=True).stdout
 import io,tarfile
 with tarfile.open(fileobj=io.BytesIO(archive)) as f:f.extractall(site,filter='data')
 handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
 server=http.server.ThreadingHTTPServer(('127.0.0.1',8766),handler)
 threading.Thread(target=server.serve_forever,daemon=True).start()
 base='http://127.0.0.1:8766/Dropzone/'
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();ctx=browser.new_context();page=ctx.new_page()
   page.goto(base+'?case=C08&view=notes');page.wait_for_selector('#note-opponent')
   page.fill('#note-opponent','Bestandsnotiz bleibt');page.fill('#note-field-0','Alte individuelle Taktik nicht löschen')
   page.locator('[data-note="resource0"]').check();page.locator('[data-note="score0-0"]').fill('7')
   page.locator('#offline').click()
   expect(page.locator('#offline-status')).to_contain_text('Offlinepaket gespeichert',timeout=90000)
   previous_storage=page.evaluate('Object.fromEntries(Object.entries(localStorage))')
   page.evaluate('async()=>{await navigator.serviceWorker.ready;}')
   for f in ROOT.rglob('*'):
    rel=f.relative_to(ROOT)
    if f.is_file() and '.git' not in rel.parts and 'qa-artifacts' not in rel.parts:
     dest=site/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
   page.evaluate('async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update();}')
   page.wait_for_function("async()=>{const keys=await caches.keys();if(!keys.includes('dropzone-1.1.0:/Dropzone/'))return false;const r=await (await caches.open('dropzone-1.1.0:/Dropzone/')).match(new URL('data/reference.json',location.href));return r&&(await r.json()).meta.version==='1.1';}",timeout=45000)
   page.wait_for_timeout(1000)
   page.reload();page.wait_for_selector('#note-opponent')
   expect(page.locator('#note-opponent')).to_have_value('Bestandsnotiz bleibt')
   expect(page.locator('[data-note="resource0"]')).to_be_checked()
   expect(page.locator('[data-note="score0-0"]')).to_have_value('7')
   assert previous_storage==page.evaluate('Object.fromEntries(Object.entries(localStorage))')
   page.goto(base+'?case=A01&role=defender');expect(page.locator('#roster-update')).to_contain_text('Web v1.1')
   page.locator('#offline').click();expect(page.locator('#offline-status')).to_contain_text('Web 1.1.0',timeout=90000)
   ctx.set_offline(True)
   page.goto(base+'?case=C10&role=attacker');expect(page.locator('#roster-update')).to_contain_text('Web v1.1')
   page.locator('#app .map img').evaluate('(i)=>i.decode()')
   assert 'K2 bleibt separat' not in page.locator('#app').inner_text()
   page.goto(base+'?case=C08&view=notes');expect(page.locator('#note-opponent')).to_have_value('Bestandsnotiz bleibt')
   page.screenshot(path=str(OUT/'upgrade-notes.png'),full_page=True)
   report={'passed':True,'oldVersion':'1.0','newVersion':'1.1','notesUnchanged':True,'checks':['actual old service worker and full offline package','existing note text, resource checkbox and score survive','new roster shown online','updated full package shown offline including previously unopened scenario']}
   (OUT/'upgrade-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
   browser.close()
 finally:server.shutdown()
