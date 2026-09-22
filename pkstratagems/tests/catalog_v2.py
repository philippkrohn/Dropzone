from pathlib import Path
import json,re,hashlib,collections
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1];C=json.loads((R/'library/catalog.json').read_text());B=json.loads((R/'quiz/data/bank.json').read_text())
assert len(C['factions'])==24
assert len([d for d in C['detachments'] if not d.get('archived')])==270
D={d['id']:d for d in C['detachments']};assert len(D)==len(C['detachments'])
S=C['stratagems'];assert len({s['id'] for s in S})==len(S)
for s in S:
 assert s['det']=='core' or s['det'] in D
 assert s['when'] and s['target'] and s['effect'][0],s['name']
 assert s['usable'],s['name']
for f in C['factions']:
 assert len(f['rulesHtml'])>100
 soup=BeautifulSoup(f['rulesHtml'],'html.parser')
 assert not soup.select('script,iframe,style,button,input')
 for el in soup.find_all(True):
  assert not any(k.lower().startswith('on') for k in el.attrs)
  if el.name=='img':assert el['src'].startswith('https://wahapedia.ru/')
for d in C['detachments']:
 if not d.get('archived'):assert d['rules'] and (any(s['det']==d['id'] for s in S) or d.get('stratagemNote')),d['name']
# Source-unchanged question facts and equal-structure answer checks.
assert len(B['questions'])>6000
bykey=collections.Counter();longest=collections.Counter();values=collections.Counter()
for q in B['questions']:
 opts=q['options'];correct=next(o for o in opts if o['id']==q['correctOptionId']);lens=[len(o['text']) for o in opts]
 if len(set(lens))>1:
  longest['n']+=1;longest['correct-longest']+=len(correct['text'])==max(lens)
 if q['topic']=='datasheet' and q['difficulty']=='easy':
  nums=[int(o['text']) for o in opts];v=int(correct['text']);values[['lowest','middle','highest'][sorted(nums).index(v)]]+=1
 bykey[q['correctOptionId']]+=1
assert all(values[k]>100 for k in ['lowest','middle','highest']),values
assert all(bykey[k]>1000 for k in ['a','b','c'])
assert 'pk_active_v2' in (R/'index.html').read_text() and 'pk_cp' in (R/'index.html').read_text()
assert 'https://6ab1939ae68f1a942996df56--pkstratagems.netlify.app/:splat 200' in (R/'netlify-site/public/_redirects').read_text()
report={'passed':True,'factions':24,'detachments':270,'stratagems':sum(bool(s.get('sourceId')) for s in S),'questions':len(B['questions']),'answerKeys':dict(bykey),'profileCorrectNumericRank':dict(values),'longestOptionAudit':dict(longest),'note':'Automatische Strukturprüfung; keine Behauptung einer fachlichen Einzelprüfung aller importierten Regeln.'}
(R/'qa').mkdir(exist_ok=True);(R/'qa/catalog-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
