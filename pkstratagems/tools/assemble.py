"""Additive PK integration; all legacy URLs fall back to the pinned old deploy."""
from pathlib import Path
import hashlib,urllib.request,re,shutil,json
ROOT=Path(__file__).resolve().parents[1]
OLD='https://6aaaf71c159714ef2f9ac9f5--pkstratagems.netlify.app'
EXPECTED='2d9bc0e99c499dd5ef5fcdae1c154e08db1738aa749c26e50c77ff8a23cf024b'
original=urllib.request.urlopen(OLD+'/',timeout=30).read()
assert hashlib.sha256(original).hexdigest()==EXPECTED,'Snapshot differs; stop rather than overwrite.'
text=original.decode()
assert text.count('</style>')==1 and text.count('</header>')==1
css='''
/* Additive section navigation; legacy application script and data unchanged. */
.hdr-in .doubles-link{display:none}
.section-links{max-width:680px;margin:0 auto;padding:0 14px 9px;display:flex;gap:8px;position:static}
.section-links a{flex:1;display:flex;align-items:center;justify-content:center;min-height:40px;padding:7px 10px;border:1px solid var(--line);border-radius:9px;color:var(--dim);text-decoration:none;font-size:.76rem;font-weight:600;text-align:center}
.section-links a[aria-current=page]{color:var(--bone);background:var(--panel-2)}
.section-links a.quiz-link{border-color:#D9B36C66;color:var(--gold)}
.section-links a:hover,.section-links a:focus-visible{background:var(--panel-2);outline:2px solid var(--gold);outline-offset:2px}
@media(max-width:380px){.hdr-in{gap:8px}.brand{gap:7px}.brand svg{width:24px;height:24px}.brand h1{font-size:.91rem;letter-spacing:.09em}.cp button{width:29px;height:32px}.cp .val{min-width:40px}}
'''
nav='<nav class="section-links" aria-label="Bereiche"><a href="./" aria-current="page">Stratagems</a><a href="doubles/">Doubles</a><a class="quiz-link" href="quiz/">Quiz-Training</a></nav>\n'
updated=text.replace('</style>',css+'</style>').replace('</header>',nav+'</header>')
assert re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.S)==re.findall(r'<script\b[^>]*>(.*?)</script>',updated,re.S)
(ROOT/'index.html').write_text(updated)
# Reproducible remote source upload, no secrets and no source PDFs included.
out=ROOT/'netlify-site';(out/'public').mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'index.html',out/'public/index.html')
shutil.copytree(ROOT/'quiz',out/'public/quiz',dirs_exist_ok=True)
(out/'public/_redirects').write_text(f'/* {OLD}/:splat 200\n')
(out/'netlify.toml').write_text('[build]\n  publish = "public"\n  command = "echo Static PK Stratagems quiz integration"\n')
report={'previousDeploy':'6aaaf71c159714ef2f9ac9f5','previousUrl':OLD,'previousRootSHA256':EXPECTED,'newRootSHA256':hashlib.sha256(updated.encode()).hexdigest(),'legacyScriptUnchanged':True,'legacyFallback':OLD+'/:splat','newRoute':'/quiz/'}
(ROOT/'integration-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
