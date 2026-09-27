"""Publish the approved bundle and verify only the recorded public website files.
The Netlify CLI creates .netlify/state.json locally during deployment. This is
not a shipped website asset and must not trigger a false rollback.
"""
import concurrent.futures,json,runpy,subprocess,sys,time
from pathlib import Path
m=runpy.run_path(str(Path(__file__).with_name('promote_preview.py')))
def verify_snapshot():
    expected=json.loads((m['EVIDENCE']/'files.json').read_text())
    excluded={'_redirects','_headers','netlify.toml'}
    assert expected and 'index.html' in expected and 'doubles/index.html' in expected
    assert not any(path.startswith('.netlify/') for path in expected)
    for path,digest in expected.items():
        assert m['sha']((m['SITE']/path).read_bytes())==digest,'Prepared website changed: '+path
    def check(item):
        path,digest=item
        if path in excluded:return
        for attempt in range(8):
            if m['sha'](m['get'](m['web'](m['PRODUCTION'],path),attempts=2))==digest:return
            time.sleep(4)
        raise AssertionError('Published website differs: '+path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(check,expected.items()))
    subprocess.run([sys.executable,str(m['PK']/'tests/browser_v2.py'),'--base',m['PRODUCTION'],'--public'],check=True,cwd=m['ROOT'])
    return len(expected)-sum(path in expected for path in excluded)
m['publish'].__globals__['verify_live']=verify_snapshot
m['publish']()
