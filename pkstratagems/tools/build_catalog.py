from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
import json,re,hashlib,html,collections,copy
ROOT=Path('pkstratagems'); SRC=Path('structured-sources'); HTML=Path('training-sources/factions'); OUT=ROOT/'library';OUT.mkdir(exist_ok=True)
# The documented export is pipe-separated and permits literal newlines inside HTML fields.
def records(name):
 raw=(SRC/(name+'.csv')).read_text(encoding='utf-8-sig');lines=raw.splitlines();head=lines.pop(0).split('|')[:-1];out=[];buffer=[]
 for line in lines:
  buffer.append(line)
  if not line.endswith('|'):continue
  record='\n'.join(buffer).split('|')[:-1];buffer=[]
  if len(record)!=len(head):raise ValueError((name,len(record),len(head),str(record)[:100]))
  out.append(dict(zip(head,record)))
 assert not buffer,name
 return out
D={p.stem:records(p.stem) for p in SRC.glob('*.csv')};Path('source-db.json').write_text(json.dumps(D,ensure_ascii=False))

def text(value):
 s=BeautifulSoup(value or '', 'html.parser')
 for e in s.select('script,style,.ShowFluff,.tooltip_templates,.noprint'):e.decompose()
 return re.sub(r'\s+',' ',s.get_text(' ',strip=True)).strip()
def clean(value,base):
 s=BeautifulSoup(value or '', 'html.parser')
 for e in s.select('script,style,iframe,input,button,svg,.ShowFluff,.tooltip_templates,.noprint,.btnFaqErrataToggle'):e.decompose()
 allowed={'p','ul','ol','li','table','thead','tbody','tr','td','th','strong','b','em','i','u','br','a','h3','h4','h5'}
 for e in list(s.find_all(True)):
  if e.name=='img':
   src=urljoin(base,e.get('src',''))
   m=re.search(r'/d([1-6])\.png$',src)
   if m:e.replace_with(m[1])
   elif src.startswith('https://wahapedia.ru/'):
    e.attrs={'src':src,'alt':e.get('alt','Regelabbildung im Original'),'loading':'lazy'}
   else:e.decompose()
  elif e.name=='a':
   href=urljoin(base,e.get('href',''))
   if href.startswith('https://wahapedia.ru/') or href.startswith('https://assets.warhammer-community.com/'):
    e.attrs={'href':href,'target':'_blank','rel':'noopener noreferrer'}
   else:e.unwrap()
  elif e.name in allowed:e.attrs={k:v for k,v in e.attrs.items() if k in ['rowspan','colspan']}
  else:e.unwrap()
 return str(s)
def norm(s):return re.sub(r'[^a-z0-9]','',s.lower())
def anchor(name):return re.sub('[^A-Za-z0-9-]','-',name).strip('-')
LEG=json.load(open('old-db.json'))
oldf={'AC':'custodes','AE':'aeldari','TYR':'tyranids','ORK':'orks','SM':'marines','AoI':'agents','CD':'daemons','WE':'worldeaters','DRU':'drukhari','NEC':'necrons','QI':'knights','AM':'guard'}
F=[];roots={};positions={};primary_names={};root_anchors={}
for f in D['Factions']:
 slug=f['link'].rstrip('/').split('/')[-1];path=HTML/(slug+'.html')
 if not path.exists():continue
 s=BeautifulSoup(path.read_text(),'html.parser');roots[f['id']]=s
 ids={norm(e.get_text(' ',strip=True)):e.get('id') for e in s.select('h3[id],h4[id]')}
 root_anchors[f['id']]=ids
 aid=s.find(id='Army-Rules');nodes=[]
 for sib in aid.next_siblings:
  if getattr(sib,'name',None) and (sib.get('data-f') or sib.name=='hr'):break
  if getattr(sib,'name',None) and 'FiltersMultiOuter' in sib.get('class',[]):continue
  nodes.append(str(sib))
 rules_html=clean(''.join(nodes),f['link']+'/')
 # For Titanicus the rule block is before hr; do not capture footer/tooltips.
 hs=[e for e in BeautifulSoup(rules_html,'html.parser').select('h3') if e.get_text(' ',strip=True) not in ['FAQ','FAQ / Errata','Errata']]
 primary_names[f['id']]=[e.get_text(' ',strip=True) for e in hs]
 F.append({'id':oldf.get(f['id'],slug),'sourceId':f['id'],'name':f['name'],'url':f['link']+'/','rulesHtml':rules_html,'ruleNames':primary_names[f['id']],'rulesBasis':'Wahapedia 11. Edition · Seitenabruf 22.09.2026','officialSourceUrls':sorted(set(a['href'] for a in s.select('a[href]') if a['href'].startswith('https://assets.warhammer-community.com/') and '.pdf' in a['href']))})
fm={f['sourceId']:f for f in F}
source={x['id']:x for x in D['Source']}
old_det={ (x['faction'],norm(x['name'])):x for x in LEG['detachments'] if x['id']!='core'}
DETS=[];det_by_source={};byfid=collections.defaultdict(list)
for d in D['Detachments']:
 if d['type'] or d['faction_id'] not in fm:continue
 f=fm[d['faction_id']];old=old_det.get((f['id'],norm(d['name'])))
 # Preserve established selector/storage ids. Alternative filter caption is not an invented detachment.
 candidates=[e for e in roots[d['faction_id']].select('h2.outline_header') if e.select_one('.dpPts')]
 match=next((e for e in candidates if norm(re.sub(r'\s*\d+DP.*$','',e.get_text(' ',strip=True)))==norm(d['name'])),None)
 if not match and d['name']=='Gladius Strike Force':match=next((e for e in candidates if e.get('id')=='Gladius-Task-Force'),None)
 if match is None:raise ValueError('No HTML detachment confirmation: '+d['name'])
 if not old:old=old_det.get((f['id'],norm(re.sub(r'\s*\d+DP.*$','',match.get_text(' ',strip=True)))))
 ab=[x for x in D['Detachment_abilities'] if x['detachment_id']==d['id']]
 enhancements=[x for x in D['Enhancements'] if x['detachment_id']==d['id']]
 det={'id':old['id'] if old else 'det-'+d['id'],'sourceId':d['id'],'faction':f['id'],'name':d['name'],'short':old.get('short',d['name']) if old else d['name'],'color':old.get('color','#C4A46A') if old else '#C4A46A','dp':int(d['dp']) if d['dp'].isdigit() else None,'disp':[v.strip() for v in d['force_disposition'].split(',') if v.strip()],'url':f['url']+'#'+match['id'],'rules':[{'name':a['name'],'html':clean(a['description'],f['url']),'text':text(a['description'])} for a in ab], 'enhancements':[{'id':e['id'],'name':e['name'],'html':clean(e['description'],f['url']),'cost':e['cost'],'upgrade':e['upgrade']=='true'} for e in enhancements]}
 det['rule']='\n\n'.join(a['name']+': '+a['text'] for a in det['rules'])
 if old:
  for prop in ['uniq','perks']:
   if prop in old:det[prop]=old[prop]
 # Restriction tags on original matched-play heading block.
 cl=match.find_parent(class_='clFl');tags=[]
 if cl:
  for t in cl.select('.detUnique,.detUniqueText'):tags.append(t.get_text(' ',strip=True))
 det['chapterDp']=[{'keyword':v['keyword'],'dp':int(v['dp'])} for v in D['Detachments_chapter_dp'] if v['detachment_id']==d['id']]
 if det['chapterDp']:det['perks']='Abweichende DP: '+', '.join(v['keyword']+' '+str(v['dp']) for v in det['chapterDp'])
 DETS.append(det);det_by_source[d['id']]=det;byfid[f['id']].append(det)
# Resolve stratagem fields from actual text, not broad export turn label (e.g. own shooting + either fight).
PHASES=['command','movement','shooting','charge','fight']
def parts(raw):
 t=text(raw); matches=list(re.finditer(r'\b(WHEN|TARGET|EFFECT|RESTRICTIONS|RESTRICTION)\s*:\s*',t));r={}
 for i,m in enumerate(matches):r[m[1].lower()]=t[m.end():matches[i+1].start() if i+1<len(matches) else len(t)].strip()
 return r
S=[];unknown=[]
for x in D['Stratagems']:
 d=det_by_source.get(x['detachment_id']);core=(x['type']=='Core Stratagem')
 if not d and not core:continue
 p=parts(x['description']);when=p.get('when','');uses=[]
 if 'any phase' in when.lower():uses=[{'p':a,'t':b} for a in PHASES for b in ['your','opp']]
 else:
  # A phase qualifier propagates across "or" unless the second says "the Fight phase".
  for phase in PHASES:
   for m in re.finditer(r'(?:(your opponent[’\']s|opponent[’\']s|your|the)\s+)?'+phase+r'\s+phase',when,re.I):
    qualifier=(m[1] or '').lower();prefix=when[:m.start()].lower()
    if qualifier=='your':turns=['your']
    elif 'opponent' in qualifier:turns=['opp']
    elif phase=='fight':turns=['your','opp']
    else:
     qs=list(re.finditer(r'your opponent[’\']s|your',prefix));last=qs[-1][0] if qs else ''
     turns=['opp'] if 'opponent' in last else ['your'] if last=='your' else ['your','opp']
    uses.extend({'p':phase,'t':t} for t in turns)
  if not uses:
   pp=[a for a in PHASES if a in (x['phase']or'').lower()];turns=['your'] if x['turn']=='Your turn' else ['opp'] if x['turn']=='Opponent’s turn' else ['your','opp']
   uses=[{'p':a,'t':t} for a in pp for t in turns];unknown.append({'id':x['id'],'when':when})
 uses=[dict(p=a,t=b) for a,b in sorted(set((u['p'],u['t']) for u in uses))]
 old=next((s for s in LEG['stratagems'] if s['det']==(d['id'] if d else 'core') and norm(s['name'])==norm(x['name'])),None)
 url=(fm[x['faction_id']]['url'] if d else 'https://wahapedia.ru/wh40k11ed/the-rules/core-rules/')+'#'+anchor(x['name'])
 entry={'id':old['id'] if old else 'str-'+x['id'],'sourceId':x['id'],'det':d['id'] if d else 'core','name':x['name'],'cp':int(x['cp_cost']) if x['cp_cost'].isdigit() else 0,'cat':x['type'].split(' – ')[-1],'gist':'Regeltext (EN) · 11. Edition','usable':uses,'when':p.get('when',''),'target':p.get('target',''),'effect':[p.get('effect','')],'restr':p.get('restrictions',p.get('restriction','')),'sourceUrl':url,'sourceBasis':'Wahapedia-Datenexport · Stand 13.09.2026, abgerufen 22.09.2026','rawText':text(x['description'])}
 if '+1CP' in entry['rawText']:entry['cpNote']='Zusatzoption +1 CP: genauen Effekt beachten.'
 if re.search(r'End of (?:your opponent[’\']s|your|the) turn',when,re.I):entry['usable']=[{'p':'turnend','t':'opp' if 'opponent' in when else 'your'}]
 if 'Reinforcements step' in when:entry['sourceWarning']='Übergangsbegriff im Quelltext: Reinforcements step. Vor Verwendung mit aktuellen Regeln/Event-FAQ abgleichen.'
 if x['name']=='EMPEROR’S WILL':entry['sourceWarning']='Quelltext nennt eine Schusserlaubnis bis zum Ende der Bewegungsphase. Dauer ist unklar; nicht im Quiz verwendet.'
 if not entry['when'] or not entry['target'] or not entry['effect'][0]:unknown.append({'id':x['id'],'missingFields':True})
 S.append(entry)
# Only currently source-backed detachment entries are active. Archive removed old detachments explicitly.
active_ids={d['id'] for d in DETS};archive=[d for d in LEG['detachments'] if d['id']!='core' and d['id'] not in active_ids]
for d in archive:
 d=copy.deepcopy(d);d['name']+=' [Archiv]';d['archived']=True;d['perks']='Alter Website-Stand. Nicht im aktuellen 11.-Editions-Katalog bestätigt.';DETS.append(d)
 for x in LEG['stratagems']:
  if x['det']==d['id']:v=copy.deepcopy(x);v['gist']='ARCHIV · nicht für aktuelles Regeltraining';v['sourceBasis']='Ungeprüfter früherer Website-Stand';S.append(v)
# Identify valid non-Legends datasheets with authoritative source listing, not source-edition guess alone.
valid_ids=set();DS=[]
for d in D['Datasheets']:
 if d['faction_id'] not in fm or d['virtual']!='false':continue
 sc=source.get(d['source_id'],{})
 if 'Legends' in sc.get('name','') or sc.get('edition') not in ['11','0']:continue
 if sc.get('edition')=='0' and '(Forge World)' not in sc.get('name',''):continue
 profiles=[r for r in D['Datasheets_models'] if r['datasheet_id']==d['id']]
 weapons=[r for r in D['Datasheets_wargear'] if r['datasheet_id']==d['id']]
 abs=[r for r in D['Datasheets_abilities'] if r['datasheet_id']==d['id'] and r['type'] not in ['Core','Faction'] and r['description']]
 DS.append({'id':d['id'],'faction':fm[d['faction_id']]['id'],'name':d['name'],'url':d['link'],'profiles':[{k:r[k] for k in ['name','M','T','Sv','W','Ld','OC','inv_sv']} for r in profiles],'weapons':[{k:r[k] for k in ['name','type','A','BS_WS','S','AP','D','range','description']} for r in weapons],'abilities':[{'name':r['name'],'text':text(r['description'])} for r in abs], 'transport':text(d['transport'])})
for f in F:
 f['detachmentIds']=[d['id'] for d in DETS if d['faction']==f['id'] and not d.get('archived')];f['datasheetIds']=[d['id'] for d in DS if d['faction']==f['id']]
 f['note']='Adeptus Titanicus führt im erfassten Regelkatalog keine eigenen Detachments. Fraktionsregeln und Datasheets sind verfügbar.' if not f['detachmentIds'] else ''
meta={'version':'2.0.0','publishedDate':'22.09.2026','edition':'11','exportLastUpdated':D['Last_update'][0]['last_update'],'retrievedDate':'22.09.2026','basis':'Quellengetreuer EN-Regeltext aus dem Wahapedia-Datenexport; Fraktionsregeln aus den am 22.09.2026 abgerufenen Seiten. Keine offizielle GW-App. Im Streitfall gelten Originalregeln und Evententscheid.','excluded':'Boarding Actions, Crusade, Legends und Unbound Adversaries sind nicht Teil des Matched-Play-Trainings. Space-Marine-Supplements werden im Quellenkatalog unter Space Marines geführt.','counts':{'factions':len(F),'detachments':len(active_ids),'stratagems':len([s for s in S if s.get('sourceId')]),'datasheets':len(DS)},'dataExport':'https://wahapedia.ru/wh40k11ed/the-rules/data-export/'}
cat={'meta':meta,'factions':F,'detachments':DETS,'stratagems':S,'datasheets':DS}
(OUT/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,separators=(',',':'))+'\n')
# A separate synchronous tiny-ish file extends the legacy browser without rewriting its storage/controls.
merged={'factions':[{'id':f['id'],'name':f['name']} for f in F],'detachments':[d for d in LEG['detachments'] if d['id']=='core']+DETS,'stratagems':S}
for d in merged['detachments']:
 for k in ['rules','enhancements','chapterDp']:d.pop(k,None)
 if 'perks' in d and isinstance(d['perks'],str):d['perks']=[d['perks']]
 if 'perks' in d:d['perks']=[html.escape(str(t)) for t in d['perks']]
 if isinstance(d.get('disp'),list):d['disp']=' · '.join(d['disp'])
 for k in ['name','short','rule','uniq']:
  if k in d:d[k]=html.escape(str(d[k]))
for s in merged['stratagems']:
 for k in ['name','gist','cat','when','target','restr','sourceBasis']:
  if k in s:s[k]=html.escape(str(s[k]))
 s['effect']=[html.escape(t) for t in s['effect']]
(OUT/'browser-data.js').write_text('/* Source-backed Matched Play catalogue; lore omitted. */\nwindow.PK_CATALOG='+json.dumps(merged,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n')
(OUT/'provenance.json').write_text(json.dumps({'meta':meta,'sourceFiles':json.load(open(SRC/'report.json')),'htmlSourceFiles':json.load(open('training-sources/fetch-report.json')),'archive':archive,'phaseFallbacks':unknown},ensure_ascii=False,indent=2))
print(meta);print('archive',archive);print('fallback',unknown[:30]);print('bytes', (OUT/'catalog.json').stat().st_size)
