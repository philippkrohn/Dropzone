"""Verify the exact authorized public artifact, not Netlify CLI runtime files.
The CLI creates .netlify/state.json locally after upload; it is not a public
website file and must never enter the publication manifest or an archive.
"""
import concurrent.futures, json, runpy, subprocess, sys, time
from pathlib import Path
m=runpy.run_path(str(Path(__file__).with_name('promote_preview.py')))
def verify_live():
    files=json.loads((m['EVIDENCE']/'files.json').read_text())
    assert len(files)>100 and all(not p.startswith('.netlify/') for p in files)
    for path,digest in files.items():
        m['safe_path'](path)
        assert m['sha']((m['SITE']/path).read_bytes())==digest,'Authorized local file changed: '+path
    public=[(p,h) for p,h in files.items() if p not in ['_redirects','_headers','netlify.toml']]
    def verify_one(item):
        path,digest=item
        for n in range(8):
            try:
                if m['sha'](m['get'](m['web'](m['PRODUCTION'],path),attempts=2))==digest:return
            except RuntimeError:
                if n==7:raise
            time.sleep(4)
        raise AssertionError('Published file differs: '+path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(verify_one,public))
    subprocess.run([sys.executable,str(m['PK']/'tests/browser_v2.py'),'--base',m['PRODUCTION'],'--public'],check=True,cwd=m['ROOT'])
    (m['EVIDENCE']/'live-integrity.json').write_text(json.dumps({'passed':True,'matchedFiles':len(public),'ignoredRuntimeFiles':['.netlify/state.json'],'basis':'immutable pre-upload manifest; each local and live public file checked'},indent=2))
    return len(public)
m['publish'].__globals__['verify_live']=verify_live
m['publish']()
