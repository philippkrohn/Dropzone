"""Preserve the existing PK interface and legacy routes; extend only intended catalogue/training."""
from pathlib import Path
import json,hashlib,re,shutil,urllib.request,html
ROOT=Path(__file__).resolve().parents[1]
PIN='https://6ab1939ae68f1a942996df56--pkstratagems.netlify.app'
HASH='63f0cf70824be2dd82b668b594a90a4c9f984d58a778e5a076c174887f396f58'
# Existing tracked root is the same checked snapshot; avoids network for local build.
p=ROOT/'index.html';raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=HASH:
 old=ROOT/'legacy-index.html'
 if old.exists():raw=old.read_bytes()
 else:raw=urllib.request.urlopen(PIN+'/',timeout=45).read()
assert hashlib.sha256(raw).hexdigest()==HASH,'Production baseline differs.'
(ROOT/'legacy-index.html').write_bytes(raw)
s=raw.decode()
assert s.count('/* ---------- Zustand ---------- */')==1
s=s.replace('/* ---------- Zustand ---------- */','''/* Catalogue v2: preserve detachment IDs, selected sources and pk_cp state. */
if(window.PK_CATALOG){
 DB.factions=window.PK_CATALOG.factions;
 DB.detachments=window.PK_CATALOG.detachments;
 DB.stratagems=window.PK_CATALOG.stratagems;
 DB.phases.push({id:'turnend',label:'Zugende'});
}
/* ---------- Zustand ---------- */''')
s=s.replace('</head>','<script src="/library/browser-data.js"></script>\n</head>')
s=s.replace('<a class="quiz-link" href="quiz/">Quiz-Training</a>','<a href="fraktionen/">Fraktionsregeln</a><a class="quiz-link" href="quiz/">Quiz-Training</a>')
s=s.replace('</header>','</header><aside class="catalog-basis"><strong>24 Fraktionen · 270 Detachments</strong><span>Erweiterter Regelkatalog (EN) · 11. Edition · <a href="fraktionen/#sources">Quellen & Stand</a></span></aside>')
s=s.replace('    </dl>`;','''      ${s.sourceWarning ? `<div class="rule-row restr"><dt>Prüfhinweis</dt><dd>${s.sourceWarning}</dd></div>` : ''}
      ${s.sourceUrl ? `<div class="rule-row"><dt>Quelle</dt><dd><a href="${s.sourceUrl}" target="_blank" rel="noopener noreferrer">Regeloriginal öffnen</a><br><small>${s.sourceBasis}</small></dd></div>` : ''}
    </dl>`;''')
s=s.replace('</style>','''
.catalog-basis{max-width:680px;margin:10px auto 0;padding:9px 14px;font-size:.71rem;color:var(--dim);display:flex;gap:5px 16px;flex-wrap:wrap}.catalog-basis strong{color:var(--gold)}.catalog-basis a{color:var(--gold)}
.section-links{flex-wrap:wrap}.section-links a{min-width:100px}.det-rule{overflow-wrap:anywhere}.gist{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.card-body a{color:var(--gold)}
@media(max-width:430px){.section-links{display:grid;grid-template-columns:1fr 1fr}.section-links a{min-width:0}#dock{overflow-x:auto;justify-content:flex-start}#dock button{flex:0 0 auto;min-width:50px}}
</style>''')
# Original state keys and interaction functions survive verbatim.
for name in ['function loadActive(){','let cp = load("pk_cp", 0);','const active = loadActive();','function toggleDet(']:assert name in s,name
(ROOT/'index.html').write_text(s)
C=json.loads((ROOT/'library/catalog.json').read_text());B=ROOT/'library/browser-data.js';t=B.read_text();prefix='window.PK_CATALOG=';start=t.index(prefix)+len(prefix);data=json.loads(t[start:].strip().rstrip(';'))
for v in data['stratagems']:
 if v.get('sourceId'):
  ef=v.get('effect',[''])[0]
  ef=re.sub(r'^Until (?:the end|the start) of [^,]+,\s*','',ef)
  v['gist']=ef[:160]+('…' if len(ef)>160 else '')
 # Warning strings come from trusted build metadata, not raw source HTML.
B.write_text('/* Mechanical data only; see provenance.json. */\nwindow.PK_CATALOG='+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n')
out=ROOT/'netlify-site';shutil.rmtree(out,ignore_errors=True);pub=out/'public';pub.mkdir(parents=True)
shutil.copy2(ROOT/'index.html',pub/'index.html')
for d in ['quiz','library','fraktionen']:shutil.copytree(ROOT/d,pub/d)
# Historical files, Doubles pages and downloads remain exactly on the pinned immutable deploy.
(pub/'_redirects').write_text(f'/* {PIN}/:splat 200\n')
(out/'netlify.toml').write_text('[build]\n publish="public"\n command="echo PK Stratagems training and faction catalogue"\n')
report={'version':'2.0.0','baseline':PIN,'baselineSHA256':HASH,'newRootSHA256':hashlib.sha256(s.encode()).hexdigest(),'counts':C['meta']['counts'],'changed':['stratagem catalogue','faction rules route','ten-question training'],'unchanged':['pk_cp','pk_active_v2','doubles fallback','Dropzone main','original PDFs'],'fallback':PIN+'/:splat'}
(ROOT/'integration-report-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
