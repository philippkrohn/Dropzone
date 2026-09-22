"""Editorial guardrails applied after the source-derived generators. No sources silently edited."""
from pathlib import Path
import json,random,re,collections,hashlib
R=Path(__file__).resolve().parents[1];C=json.loads((R/'library/catalog.json').read_text());B=json.loads((R/'quiz/data/bank.json').read_text());I=json.loads((R/'quiz/data/index.json').read_text())
for d in C['detachments']:
 if not d.get('archived'):
  d.pop('uniq',None);d.pop('perks',None)
  if not any(s['det']==d['id'] for s in C['stratagems']):d['stratagemNote']='Der erfasste Datenexport führt für dieses Detachment keine eigenen Stratagems. Fraktionsregeln, Detachment-Regeln und Aufwertungen sind oben zugänglich; bei Bedarf das Regeloriginal prüfen.'
for s in C['stratagems']:
 if not s['usable'] and s['when']=='End of any of your phases.':s['usable']=[{'p':p,'t':'your'} for p in ['command','movement','shooting','charge','fight']]
# Use other real, similarly-sized WHEN clauses instead of making the correct timing consistently shortest.
def normal(s):return re.sub(r'[^a-z0-9]','',s.lower())
DS={d['id']:d for d in C['detachments']}
valid=[s for s in C['stratagems'] if s.get('sourceId') and not s.get('sourceWarning')]
kept=[];removed=[]
for q in B['questions']:
 if q['id'].endswith('-when'):
  sid=q['id'].removeprefix('str-').removesuffix('-when');s=next(s for s in valid if s['sourceId']==sid);true=s['when'];fid=DS.get(s['det'],{}).get('faction')
  candidates={v['when'] for v in valid if DS.get(v['det'],{}).get('faction')==fid and normal(v['when'])!=normal(true) and abs(len(v['when'])-len(true))<=max(8,len(true)*.22)}
  if len(candidates)<2:
   candidates={v['when'] for v in valid if normal(v['when'])!=normal(true) and abs(len(v['when'])-len(true))<=max(5,len(true)*.15)}
  # Normalize apostrophe variants and avoid two equivalent alternative quotes.
  unique={normal(v):v for v in sorted(candidates)}
  if len(unique)<2:removed.append(q['id']);continue
  r=random.Random(q['id']);others=r.sample(list(unique.values()),2);vals=[true,*others];r.shuffle(vals)
  q['options']=[{'id':chr(97+i),'text':v} for i,v in enumerate(vals)];q['correctOptionId']=chr(97+vals.index(true))
  q['prompt']=f"{s['name']}: Welche Angabe aus dem WHEN-Abschnitt gehört im erfassten Regeltext zu diesem Stratagem?"
  q['explanation']='Entscheidend ist die vollständige Timing-Angabe, nicht nur eine ähnliche Phase. Die anderen Antworten stammen aus anderen Regeltexten. Hier gilt: '+true
 kept.append(q)
for q in kept:
 if q['id']=='tactics-e04':q['options'][2]['text']='Den Angriff zunächst ganz zurückhalten.'
 if q['id']=='tactics-h09':q['prompt']=q['prompt'].replace('Du kannst X erst nach Y aktivieren.','X kann nach Y noch aktiviert werden.')
B['questions']=kept
I['allQuestions']=len(kept);I['counts']=dict(collections.Counter(q['difficulty'] for q in kept))
for file,data in [('library/catalog.json',C),('quiz/data/bank.json',B),('quiz/data/index.json',I)]: (R/file).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
p=R/'library/browser-data.js';s=p.read_text();a=s.index('window.PK_CATALOG=')+len('window.PK_CATALOG=');D=json.loads(s[a:].strip().rstrip(';'));m={x['id']:x for x in C['stratagems']}
for x in D['stratagems']:x['usable']=m[x['id']]['usable']
for d in D['detachments']:
 if d['id']!='core' and not d.get('archived'):d.pop('uniq',None);d.pop('perks',None)
p.write_text('window.PK_CATALOG='+json.dumps(D,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n')
print('Comparable WHEN choices, current-only metadata and explicit missing own-stratagem notes applied.',len(kept),'questions;',len(removed),'unbalanced WHEN variants omitted.')
