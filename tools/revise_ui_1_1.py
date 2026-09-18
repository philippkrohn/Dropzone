from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
p=R/'app.mjs';s=p.read_text()
def replace(old,new):
 global s
 assert old in s,old[:130]
 s=s.replace(old,new)
replace("const APP_VERSION = '1.0.0';","const APP_VERSION = '1.1.0';")
replace("'Reserven und Rhino-Belegung festgelegt'","'K1 → V1 / K2 → V2, Reserven und Rhino-Belegung festgelegt'")
start=s.index('function legendHTML()');end=s.index('function box(',start)
s=s[:start]+'''function legendHTML() {return `<div class="legend" aria-label="Einheitenlegende">${Object.entries(ref.legend).map(([n,units])=>`<button data-anchor="${n}"><span class="number ${+n>=6?'philipp':''}">${n}</span><span>${h(units.join(' + '))}<small>${n==='4'?'S1 startet im Rhino':['7','8'].includes(n)?'Eine Attached Unit · 4 Modelle · 355 P.':+n>=6?'Philipp · 3 Guardian Spears':'Norman · Agenten'}</small></span></button>`).join('')}</div><p class="legend-description">Zahlen = Bereitstellungsräume, keine maßstäblichen Bases. <strong>Anker 7 und 8: jeweils eine angeschlossene Vierer-Bike-Einheit.</strong> K1 führt V1; K2 führt V2. Andere zusammen aufgeführte Trupps bleiben getrennt; S1 sitzt im Rhino. T1/T2: je drei Guardian Spears, ohne Vexilla. <strong>Reserve-Empfehlung:</strong> B2 (145 P.) und T2 (165 P.).</p>`;}
function revisionHTML() {return `<section class="notice roster-update" id="roster-update"><strong>${h(ref.revision.title)}</strong><p>${h(ref.revision.summary)}</p><details><summary>Folgen für Aufstellung und Boni</summary><p>${h(ref.revision.tradeoff)}</p><p>${h(ref.revision.rules)}</p><p class="small">${h(ref.revision.source)} Das ursprüngliche PDF bleibt auf v1.0.</p></details></section>`;}
''' +s[end:]
replace('Anker: Einsatzdossier v1.0, Seite ${c.pdfpage}.','Bereitstellungsräume aus Dossier v1.0, Seite ${c.pdfpage}; Einheitenbelegung aktualisiert auf Web v1.1.')
replace("${box('Seiten & Zugänge',c.role_note)}","${box('Seiten & Zugänge',c.role_note)}${box('Vierer-Einheiten in diesem Layout',c.formation_note)}")
replace("${box('Formation · Empfehlung, keine Pflicht','S1 im Rhino. B2 in Normans Reserve, T2 in Philipps Reserve. Gegen starken frühen Druck bei Gather Intel oder Vital Link kann T2 bereits auf dem Tisch beginnen. Beide Captains zunächst separat und geschützt halten.')}","${box('Startanschlüsse fest · Reserve als Empfehlung',ref.revision.formation)}")
replace('Einsatzdossier v1.0, Seite ${m.pdfpage} · ${h(m.source)}.','Web-Taktik v1.1 · ${h(m.revisionSource)} · Missionsquelle: ${h(m.source)}. Das PDF v1.0 (S.${m.pdfpage}) enthält noch den älteren Plan.')
a=s.index('function unitsHTML()');b=s.index('function sourcesHTML()',a)
s=s[:a]+'''function unitsHTML() {return `<p class="small">Nach allen Startanschlüssen: ${ref.deployment.teamFormations} Team-Einheiten, davon ${ref.deployment.custodesFormations} Custodes-Einheiten. Die sechs Custodes-Listeneinträge sind unten zu ihren vier Spielformationen zusammengefasst.</p><div class="unit-grid">${ref.formations.map(u=>`<article class="unit-card ${u.player==='Philipp'?'philipp':''}"><span class="unit-id">${h(u.id)}</span> <span class="small">${h(u.player)}</span><strong>${h(u.name)}</strong><small>${u.models} Modelle · ${u.points} Punkte</small>${u.wargear?`<p class="small">${h(u.wargear)}</p>`:''}${u.components.length>1?`<p class="small">Bestandteile: ${u.components.map(id=>{const v=ref.units.find(x=>x.id===id);return h(id)+': '+v.points+' P.';}).join(' + ')}</p>`:''}</article>`).join('')}</div>`;}
''' +s[b:]
replace('Der Quellenstand bleibt 16.09.2026; dies ist keine erneute Freigabe zum 03.10.2026.','Regel- und Missionsbasis: 16.09.2026. L-18 bezeichnet Philipps neue Custodes-Liste und die daraus abgeleitete Web-Taktik vom 18.09.2026. Dies ist keine erneute Regelfreigabe zum 03.10.2026.')
replace('Die Anker entsprechen dem Dossier; die Webansicht ist keine Maßzeichnung.','Die Bereitstellungsräume stammen aus dem Dossier; ihre Einheitenbelegung entspricht der neuen Startformation. Die Webansicht ist keine Maßzeichnung.')
replace('1.040 Punkte Custodes + 955 Punkte Agenten. Team-Warlord noch gemeinsam festzulegen; K1 ist nur eine Empfehlung.','1.040 Punkte Custodes + 955 Punkte Agenten. K1 ist Warlord im aktuellen Custodes-Export; die gemeinsame Team-Warlord-Wahl mit Norman abgleichen. <a href="./data/custodes-roster-2026-09-18.txt">Aktuellen Listenexport lesen</a>.')
replace("let html=selector();if(state.error)","let html=selector();if(['table','plan','rules'].includes(state.view))html+=revisionHTML();if(state.error)")
replace("${b.dataset.anchor==='4'?'S1 beginnt im Rhino.':'Räumliche Zusammenarbeit, nicht automatisch eine angeschlossene Einheit.'}","${h(ref.legendNotes[b.dataset.anchor])}")
replace('${u.player} · ${u.models} Modelle · ${u.points} Punkte</p>','${u.player} · ${u.models} Modelle · ${u.points} Punkte${u.wargear?`<br>${h(u.wargear)}`:\'\'}</p>')
replace('Webfassung ${APP_VERSION} · taktischer Inhalt v1.0, Stand 16.09.2026.','Webfassung ${APP_VERSION} · neue Custodes-Liste und Taktik 18.09.2026, Regelbasis 16.09.2026.')
replace('Quelle: Dossier S.${c.pdfpage}; Event Companion S.${c.gwpage}.','Bereitstellungsräume: Dossier v1.0 S.${c.pdfpage}; Einheitenbelegung und Taktik: Web v1.1. Event Companion S.${c.gwpage}.')
replace('<p>${h(c.role_note)}</p><h4>Wir spielen zuerst','<p>${h(c.role_note)}</p><p>${h(c.formation_note)}</p><h4>Wir spielen zuerst')
replace('${h(m.source)} · Original-Dossier S.${m.pdfpage}','${h(m.source)} · Web-Taktik v1.1 / L-18; Original-PDF unverändert')
replace('fetch(`./data/${n}.json`)','fetch(`./data/${n}.json`,{cache:\'no-cache\'})')
replace("register('./sw.js')","register('./sw.js',{updateViaCache:'none'})")
replace("'Offlinepaket gespeichert · nur auf diesem Gerät.'","'Offlinepaket gespeichert · Web '+(e.data.version??APP_VERSION)+' · nur auf diesem Gerät.'")
p.write_text(s)
p=R/'index.html';s=p.read_text().replace('Inhalt: Dossier v1.0 · 16.09.2026.','Inhalt: Web v1.1 · Listenupdate 18.09.2026. PDF v1.0 unverändert.').replace('Offlinepaket speichern','Offlinepaket speichern / aktualisieren');p.write_text(s)
p=R/'style.css';s=p.read_text();s+='\n/* Roster revision: preserve narrow-screen readability. */\n.roster-update p{margin:.65rem 0 0}.roster-update details{margin-top:.7rem}.roster-update summary{cursor:pointer;font-weight:600}.unit-card p{margin:.65rem 0 0;overflow-wrap:anywhere}\n';p.write_text(s)
p=R/'sw.js';s=p.read_text().replace("const VERSION='dropzone-1.0.0';","const VERSION='dropzone-1.1.0';")
s=s.replace("self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE.map(p=>new URL(p,ROOT).href))));});", "self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE.map(p=>new Request(new URL(p,ROOT).href,{cache:'reload'})))).then(()=>self.skipWaiting()));});")
s=s.replace("self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim());});", """// Migrate only immutable maps from prior app caches. Never migrate old rules/data.
// Browser localStorage (notes, checks, theme) is not touched.
self.addEventListener('activate',e=>{e.waitUntil((async()=>{
 const current=await caches.open(CACHE);
 for(const name of await caches.keys()){
  if(name===CACHE||!name.startsWith('dropzone-')||!name.endsWith(':'+ROOT.pathname))continue;
  const previous=await caches.open(name);
  for(const page of PAGES)for(const kind of ['board','page']){
   const key=new URL(`assets/layouts/${kind}-${page}.webp`,ROOT).href;
   if(!await current.match(key)){const image=await previous.match(key);if(image)await current.put(key,image);}
  }
 }
 await self.clients.claim();
})());});""")
s=s.replace("'data/chapters.json'];","'data/chapters.json','data/custodes-roster-2026-09-18.txt'];")
s=s.replace("port.postMessage({done:true});","port.postMessage({done:true,version:'1.1.0'});")
p.write_text(s)
(R/'data/custodes-roster-2026-09-18.txt').write_text('''+++++++++++++++++++++++++++++++++++++++++++++++
+ FACTION KEYWORD: Imperium - Adeptus Custodes
+ DETACHMENT: Auric Champions (Assemblage of Might)
+ FORCE DISPOSITION: Priority Assets
+ TOTAL ARMY POINTS: 1040pts
+
+ WARLORD: Char1: Shield-Captain on Dawneagle Jetbike
+ NUMBER OF UNITS: 6
+ SECONDARY: - Assassination: 2 Characters
+++++++++++++++++++++++++++++++++++++++++++++++

Char1: 1x Shield-Captain on Dawneagle Jetbike (140 pts): Warlord, Interceptor lance, Salvo launcher
Leading Vertus Praetors[1]
Char2: 1x Shield-Captain on Dawneagle Jetbike (140 pts): Interceptor lance, Salvo launcher
Leading Vertus Praetors[2]

3x Allarus Custodians (165 pts): 3 with Balistus grenade launcher, Guardian Spear
3x Allarus Custodians (165 pts): 3 with Balistus grenade launcher, Guardian Spear
3x Vertus Praetors (215 pts): 3 with Interceptor lance, Salvo launcher
  Attached to Shield-Captain on Dawneagle Jetbike[1]
3x Vertus Praetors (215 pts): 3 with Interceptor lance, Salvo launcher
  Attached to Shield-Captain on Dawneagle Jetbike[2]

Created with newrecruit.eu v35.82
''')
p=R/'tests/content-sha256.json';checks=json.loads(p.read_text())
for name in checks:
 value=json.loads((R/name).read_text());checks[name]=hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
p.write_text(json.dumps(checks,indent=2)+'\n')
print('Updated interface, roster export and offline cache. Original PDFs and note keys untouched.')
