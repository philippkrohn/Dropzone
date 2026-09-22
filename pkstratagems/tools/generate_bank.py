from pathlib import Path
from bs4 import BeautifulSoup
import json,re,random,math,hashlib,collections,statistics
ROOT=Path('pkstratagems');C=json.loads((ROOT/'library/catalog.json').read_text());D=json.load(open('source-db.json'));Q=json.loads((ROOT/'quiz/data/authored.json').read_text());rng=random.Random(20260922)
F={f['id']:f for f in C['factions']}; DET={d['id']:d for d in C['detachments'] if not d.get('archived')}; STR=[s for s in C['stratagems'] if s.get('sourceId') and not s.get('sourceWarning') and (s['det']=='core' or s['det'] in DET)]
def text(s):return re.sub(r'\s+',' ',BeautifulSoup(s,'html.parser').get_text(' ',strip=True)).strip()
def options(id,values):
 v=list(values);r=random.Random(id);r.shuffle(v)
 return [{'id':chr(97+i),'text':x} for i,x in enumerate(v)],chr(97+v.index(values[0]))
def add(id,concept,level,topic,prompt,values,why,url,locator,faction=None,det=None):
 if len(values)!=3 or len(set(values))!=3:return False
 opts,key=options(id,values)
 Q.append({'id':id,'conceptId':concept,'difficulty':level,'topic':topic,'kind':'rules','faction':faction,'detachment':det,'prompt':prompt,'options':opts,'correctOptionId':key,'explanation':why,'sources':[{'title':'Wahapedia · 11. Edition · Datenstand 13.09.2026','url':url,'locator':locator}]});return True

def replace_numeric(s):
 # Change one explicit quantitative rule condition, never hide a qualification only in the true option.
 matches=[m for m in re.finditer(r'(?<![A-Za-z\d])([1-9]\d?)(?=(?:\+|\"|\s*(?:CP|A\b|S\b|T\b|AP\b|D\b|mortal wounds?|wounds?|models?|dice|attacks?|battle rounds?))|\b)',s) if not re.search(r'(?:once|twice|D)$',s[max(0,m.start()-5):m.start()])]
 # Exclude numbered steps and rule-reference chapter numbers.
 matches=[m for m in matches if s[m.end():m.end()+1] not in ['.',':'] and not re.match(r'\s*[.)]',s[m.end():])]
 if not matches:return None
 m=matches[len(matches)//2];n=int(m[1]);candidates=[v for v in [n-2,n-1,n+1,n+2,n+3] if v>=1]
 if s[m.end():m.end()+1]=='+':candidates=[v for v in candidates if 2<=v<=6]
 if len(candidates)<2:return None
 choices=random.Random(s).sample(candidates,2)
 return [s,*(s[:m.start()]+str(v)+s[m.end():] for v in choices)]
# Three knowledge modes per stratagem: cost, exact trigger, multi-clause effect detail.
for s in STR:
 det=DET.get(s['det']);fid=det['faction'] if det else None;scope=det['name'] if det else 'Core Rules';base='str-'+s['sourceId'];loc=f"{scope} / {s['name']} / WHEN, TARGET, EFFECT"
 if not s.get('cpNote'):
  vals=[str(s['cp'])+' CP']+[str(v)+' CP' for v in ([2,3] if s['cp']==1 else [1,3] if s['cp']==2 else [1,2])]
  add(base+'-cost',base,'easy','stratagem',f"{scope}: Wie viele CP kostet {s['name']} ohne Rabatte oder Zuschläge?",vals,f"Der Quelltext nennt {s['cp']} CP. Voraussetzungen und Zeitpunkte gelten zusätzlich.",s['sourceUrl'],loc,fid,s['det'] if det else None)
 # Prefer close alternative trigger timings of parallel construction.
 w=s['when'];wv=None
 substitutions=[('just after','just before','at the end, after'),('End of','Start of','Middle of'),('At the start of','At the end of','During'),('at the start of','at the end of','during')]
 for term,a,b in substitutions:
  if term in w:
   # "Middle" is not a printed timing category; do not use as giveaway.
   if term=='End of':wv=[w,w.replace(term,'Start of',1),w.replace(term,'During',1)]
   elif term=='just after':wv=[w,w.replace(term,'just before',1),w.replace(term,'at the end of the phase, after',1)]
   else:wv=[w,w.replace(term,a,1),w.replace(term,b,1)]
   break
 if not wv:
  for phase in ['Movement','Shooting','Charge','Fight','Command']:
   if phase+' phase' in w:
    others=[p for p in ['Movement','Shooting','Charge','Fight','Command'] if p!=phase];r=random.Random(base);r.shuffle(others)
    wv=[w,w.replace(phase+' phase',others[0]+' phase',1),w.replace(phase+' phase',others[1]+' phase',1)];break
 if wv and max(map(len,wv))<=260 and max(map(len,wv)) <= min(map(len,wv))*1.55:
  add(base+'-when',base,'medium','stratagem',f"Welcher genaue Einsatzzeitpunkt gehört zu {s['name']} ({scope})?",wv,'Entscheidend ist der konkrete Trigger, nicht nur ein ähnlicher Phasenname. Im erfassten Text: '+w,s['sourceUrl'],loc,fid,s['det'] if det else None)
 eff=s['effect'][0];nv=replace_numeric(eff)
 if nv and len(eff)<=620:
  add(base+'-detail',base,'hard','stratagem',f"{s['name']} ({scope}): Ziel und Einsatzzeitpunkt sind erfüllt. Welche Regelnotiz gibt die Wirkung vollständig korrekt wieder?",nv,'Die entscheidende Mengen-, Entfernungs- oder Schwellenbedingung darf nicht gegen eine ähnliche Zahl ausgetauscht werden. Maßgeblicher Effekt: '+eff,s['sourceUrl'],loc,fid,s['det'] if det else None)
# Every real detachment appears with its rule/DP metadata; no invented archive entries.
for d in DET.values():
 if isinstance(d['dp'],int):
  add('det-'+d['sourceId']+'-dp','det-'+d['sourceId'],'easy','detachment',f"Wie viele DP kostet {d['name']} laut dem erfassten Katalog (ohne ausdrücklich separat aufgeführte Chapter-Abweichung)?",[f'{d["dp"]} DP']+[f'{x} DP' for x in [1,2,3,4] if x!=d['dp']][:2],f"Der Basiseintrag führt {d['dp']} DP. Chapter-spezifische Abweichungen und Kombinationsbeschränkungen sind zusätzlich zu prüfen.",d['url'],'Detachment-Katalog / DP',d['faction'],d['id'])
 for ix,a in enumerate(d['rules']):
  val=replace_numeric(a['text'])
  if val and len(a['text'])<=650:add('det-'+d['sourceId']+'-rule'+str(ix),'det-'+d['sourceId']+'-rule'+str(ix),'medium','detachment',f"{d['name']} – {a['name']}: Welche Regelnotiz stimmt?",val,'Die korrekte Regelnotiz entspricht dem erfassten Detachment-Wortlaut. '+a['text'],d['url'],a['name'],d['faction'],d['id'])
# Faction rules are selected only when they appear on that faction's army-rules page, not allied-export duplicates.
for f in F.values():
 names=f['ruleNames'];rows=[r for r in D['Abilities'] if r['faction_id']==f['sourceId'] and r['name'] in names]
 for i,a in enumerate(rows):
  t=text(a['description']);nv=replace_numeric(t)
  if nv and len(t)<=700:add('army-'+f['id']+'-'+a['id'],'army-'+f['id']+'-'+a['id'],'medium','faction',f"{f['name']} – {a['name']}: Welche Regelnotiz ist richtig?",nv,'Die Mengen- oder Reichweitenbedingung gehört zur Fraktionsregel, nicht zu einem beliebigen Detachment. '+t,f['url']+'#Army-Rules',a['name'],f['id'])
  other=[r['name'] for r in D['Abilities'] if r['faction_id'] and r['faction_id']!=f['sourceId'] and r['name'] and r['name'] not in names and 'Team' not in r['name']]
  same=[n for n in other if .65*len(a['name'])<=len(n)<=1.5*len(a['name'])];rng.shuffle(same)
  if len(set(same))>=2:add('army-'+f['id']+'-'+a['id']+'-name','army-'+f['id']+'-'+a['id'],'easy','faction',f"Welche dieser Regeln steht in der Fraktionsregelübersicht für {f['name']}?",[a['name'],*list(dict.fromkeys(same))[:2]],'Die Zuordnung lautet '+f['name']+' → '+a['name']+'. Die vollständigen Voraussetzungen stehen in der Fraktionsübersicht.',f['url']+'#Army-Rules',a['name'],f['id'])
# Datasheet profiles and probability application are explicitly scoped; no hidden unit abilities are assumed.
def numeric(s):return bool(re.fullmatch(r'\d+',s or ''))
def numchoices(v):
 others=[n for n in [v-2,v-1,v+1,v+2,v+3] if n>=1];vals=[v,*rng.sample(others,2)];return [str(x) for x in vals]
for ds in C['datasheets']:
 if not ds['profiles']:continue
 pr=ds['profiles'][0];fid=ds['faction'];base='ds-'+ds['id'];name=ds['name']
 if numeric(pr['T']):add(base+'-t',base,'easy','datasheet',f"{name}: Welchen Toughness-Wert hat das Profil „{pr['name']}“ ohne Modifikatoren?",numchoices(int(pr['T'])),'Der erfasste Profilwert ist T'+pr['T']+'. Andere Modelle oder Leader können eigene Profile haben.',ds['url'],'Datasheet / '+pr['name']+' / T',fid)
 fixed=[w for w in ds['weapons'] if all(numeric(w[k]) for k in ['A','BS_WS','S']) and w['type'] in ['Ranged','Melee'] and 2<=int(w['BS_WS'])<=6 and 1<=int(w['A'])<=24 and int(w['S'])>0]
 # Select one weapon per datasheet; avoid repetitive variants across a run (shared concept id).
 if not fixed:continue
 w=sorted(fixed,key=lambda w:(w['type']!='Melee',w['name']))[0];sval=int(w['S']);a=int(w['A']);skill=int(w['BS_WS']);target=sval+1
 required=6 if sval*2<=target else 5
 add(base+'-wound',base,'medium','datasheet',f"{name} greift mit „{w['name']}“ an. Verwende den unmodifizierten S-Wert des erfassten Waffenprofils gegen T{target}; Sonderfähigkeiten sind für dieses Rechenbeispiel ausgeschaltet. Welches Verwundungsergebnis wird benötigt?",[f'{required}+',*[f'{v}+' for v in [3,4,5,6] if v!=required][:2]],f"Das erfasste Waffenprofil hat S{sval}. Gegen T{target} liegt die Stärke darunter"+(' und höchstens bei der Hälfte.' if required==6 else ', aber über der Hälfte.')+f' Deshalb {required}+.',ds['url'],w['name']+' / S; Core Rules05.02',fid)
 # HARD: two-stage expectation with a specific reroll, not memorizing a price under a harder badge.
 hit=(7-skill)/6;wound=2/6; rerollhit=hit+(1-hit)*hit; ev=a*rerollhit*wound
 candidates=[a*hit*wound,a*rerollhit*(3/6),a*hit*(wound+(1-wound)*wound),a*rerollhit*(wound+(1-wound)*wound),a*hit*(1/6),a*rerollhit*(4/6)]
 candidates=list({round(v,2):v for v in candidates if abs(round(v,2)-round(ev,2))>.001}.values());alternatives=rng.sample(candidates,2)
 values=[f'{v:.2f}'.replace('.',',')+' erwartete Verwundungen' for v in [ev,*alternatives]]
 add(base+'-math',base,'hard','datasheet',f"Rechenmodell zu {name}, „{w['name']}“: {a} Attacken, Treffer auf {skill}+, Stärke {sval} gegen T{target}. Alle misslungenen Treffer dürfen einmal wiederholt werden; Verwundungen nicht. Sämtliche übrigen Waffen- und Einheitenfähigkeiten sind für dieses Modell ausgeschlossen. Wie viele erfolgreiche Verwundungen erwartest du vor Schutzwürfen?",values,f"P(Treffer mit Wiederholung) = {hit:.3f} + (1 − {hit:.3f}) × {hit:.3f} = {rerollhit:.3f}. P(Verwundung)=2/6"+(' (hier wäre die Hälfte-Schwelle anders, siehe Prüfung)' if required==6 else '')+f'. Ergebnis: {a} × {rerollhit:.3f} × 2/6 = {ev:.2f}. Es ist ein definiertes Rechenmodell, keine vollständige Schadensprognose dieses Datasheets.',ds['url'],w['name']+'; Modellannahmen im Fragetext; Core Rules05.01–05.02',fid)
 if required==6:Q.pop() # This corner case is not silently solved with the wrong wound probability.
# Validate and publish one bank. The UI samples exactly ten distinct concepts, not ten variants of one question.
ids=[q['id'] for q in Q];assert len(ids)==len(set(ids))
# Fix documented situational ambiguities before release.
for q in Q:
 if q['id']=='tactics-h04':q['prompt']=q['prompt'].replace('Du führst um2.','Du führst um5.')
 if q['id']=='tactics-e05':q['options'][1]['text']='Den Helfer aus beiden Räumen abziehen.'
 if q['id']=='tactics-h07':q['options'][1]['text']='Die Angriffsreserve hinter der Linie halten.'
 if q['id']=='tactics-h06':q['options'][2]['text']='Den CP bis zum Spielende ungenutzt behalten.'
 # Explanations shouldn't imply complete real-life firing profiles for synthetic math.
 # Strip gratuitous double spaces but preserve exact EN source mechanics.
 for o in q['options']:o['text']=re.sub(r'\s+',' ',o['text']).strip()
ratio=[]
for q in Q:
 lengths=[len(o['text']) for o in q['options']];r=max(lengths)/max(1,min(lengths))
 if r>1.7 and q['kind']=='tactics':ratio.append((q['id'],round(r,2),[(o['id'],o['text']) for o in q['options']]))
OUT=ROOT/'quiz/data';(OUT/'bank.json').write_text(json.dumps({'schemaVersion':2,'version':'2.0.0','sessionLength':10,'rulesBasis':C['meta'],'questions':Q},ensure_ascii=False,separators=(',',':'))+'\n')
# Listing metadata intentionally contains no pseudo-quiz for unreviewed rules or player-specific lists.
index={'schemaVersion':2,'version':'2.0.0','sessionLength':10,'bank':'bank.json','factions':[{'id':f['id'],'name':f['name'],'detachmentIds':f['detachmentIds']} for f in F.values()],'detachments':[{'id':d['id'],'name':d['name'],'faction':d['faction']} for d in DET.values()],'difficulties':{'easy':'Grundlagen','medium':'Fortgeschritten','hard':'Experte'},'topics':{'faction':'Fraktionsregeln','detachment':'Detachment-Regeln','stratagem':'Stratagems','datasheet':'Datasheets & Rechenmodelle','core':'Core Rules','tactics':'Taktikentscheidungen'},'counts':dict(collections.Counter(q['difficulty'] for q in Q)),'tacticalQuestions':sum(q['kind']=='tactics' for q in Q),'allQuestions':len(Q),'coverageNote':'Alle 24 erfassten Matched-Play-Fraktionen und 270 Detachments stehen zur Auswahl. Allgemeine Core-Rules- und Taktikfragen sind als fraktionsübergreifend gekennzeichnet. Eine engere Themenwahl startet nur bei mindestens zehn unterschiedlichen verfügbaren Konzepten.'}
(OUT/'index.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':'))+'\n')
report={'total':len(Q),'topics':dict(collections.Counter(q['topic'] for q in Q)),'difficulty':index['counts'],'tacticalLengthOutliers':ratio,'unreviewedRulesExcluded':[s['name'] for s in C['stratagems'] if s.get('sourceWarning')],'generation':'Quellengebundene Regelvarianten und ausdrücklich vereinfachte Rechenmodelle; Taktikfragen redaktionell formuliert.'}
(ROOT/'quiz/question-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
