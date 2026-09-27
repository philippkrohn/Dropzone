"""Locate the actual existing Doubles app without replacing it with the Pages app."""
import json, re, runpy
from pathlib import Path
m=runpy.run_path(str(Path(__file__).with_name('promote_preview.py')))
get=m['get']; selected=None
candidates=[m['PRODUCTION']+'doubles/',m['BASELINE']+'doubles/',m['PREVIEW']+'doubles/','https://6aaaf71c159714ef2f9ac9f5--pkstratagems.netlify.app/doubles/']
for base in candidates:
 try:
  raw=get(base,attempts=2)
  count=len(set(re.findall(r'[\"\'](daten/[^\"\']+\.json)[\"\']',raw.decode())))
  print('Doubles source',base,'bytes',len(raw),'data files',count,flush=True)
  if count==4:selected=base;break
 except Exception as e:print('Doubles source unavailable:',base,type(e).__name__,flush=True)
if selected is None:raise RuntimeError('Original Doubles source not reachable; production remains unchanged.')
def fetch_source(url,attempts=5):
 prefix=m['PREVIEW']+'doubles/'
 if url.startswith(prefix):url=selected+url[len(prefix):]
 return get(url,attempts)
m['prepare'].__globals__['get']=fetch_source
m['prepare']()
p=m['EVIDENCE']/'assembly.json';report=json.loads(p.read_text());report['doublesSource']=selected;p.write_text(json.dumps(report,indent=2))
