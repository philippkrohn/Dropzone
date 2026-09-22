"""Final typography/provenance alignment; no rule or scoring changes."""
import json,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
p=R/'quiz/data/bank.json';bank=json.loads(p.read_text())
def polish(s):
 s=re.sub(r'(?<=[a-zäöüß])(?=\d)', ' ', s)
 s=re.sub(r'(?<=\d)(?=[a-zäöüß])', ' ', s)
 return s
for q in bank['questions']:
 if q['kind']=='tactics':
  for k in ['prompt','explanation','assumptions','objective']:
   if isinstance(q.get(k),str):q[k]=polish(q[k])
  for o in q['options']:
   o['text']=polish(o['text'])
   if isinstance(o.get('explanation'),str):o['explanation']=polish(o['explanation'])
p.write_text(json.dumps(bank,ensure_ascii=False,separators=(',',':'))+'\n')
a=R/'quiz/data/authored.json';ids=[q['id'] for q in json.loads(a.read_text())];byid={q['id']:q for q in bank['questions']}
a.write_text(json.dumps([byid[i] for i in ids],ensure_ascii=False,indent=2)+'\n')
p=R/'quiz/question-audit.json';audit=json.loads(p.read_text());audit.update(total=len(bank['questions']),topics=dict(Counter(q['topic'] for q in bank['questions'])),difficulty=dict(Counter(q['difficulty'] for q in bank['questions'])))
p.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
assert len(bank['questions'])==7203
print('Aligned authored reference, typographic spacing and final coverage audit: 7203 questions.')
