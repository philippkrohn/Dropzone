const VERSION='dropzone-1.1.0';
const ROOT=new URL('./',self.location.href);
const CACHE=VERSION+':'+ROOT.pathname;
const PAGES=[18,20,22,23,30,32,34,35,39,41,43,44,45,47,48,49,50,52,53];
const CORE=['./','index.html','style.css','app.mjs','core.mjs','favicon.svg','data/cases.json','data/missions.json','data/reference.json','data/words.json','data/chapters.json','data/custodes-roster-2026-09-18.txt'];
const ALL=[...CORE,...PAGES.flatMap(p=>[`assets/layouts/board-${p}.webp`,`assets/layouts/page-${p}.webp`])].map(p=>new URL(p,ROOT).href);
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE.map(p=>new Request(new URL(p,ROOT).href,{cache:'reload'})))).then(()=>self.skipWaiting()));});
// Migrate only immutable maps from prior app caches. Never migrate old rules/data.
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
})());});
self.addEventListener('fetch',e=>{
 const u=new URL(e.request.url);if(e.request.method!=='GET'||u.origin!==ROOT.origin||!u.pathname.startsWith(ROOT.pathname))return;
 const key=e.request.mode==='navigate'?new URL('index.html',ROOT).href:e.request;
 e.respondWith((async()=>{const c=await caches.open(CACHE);try{const r=await fetch(e.request);if(r.ok)c.put(key,r.clone());return r;}catch{const hit=await c.match(key);return hit??new Response('Offline nicht gespeichert',{status:503});}})());
});
self.addEventListener('message',e=>{if(e.data?.type!=='CACHE_ALL')return;const port=e.ports[0];e.waitUntil((async()=>{try{const c=await caches.open(CACHE);let count=0;for(const url of ALL){const r=await fetch(url,{cache:'reload'});if(!r.ok)throw new Error('Mindestens eine Datei konnte nicht geladen werden.');await c.put(url,r);port.postMessage({count:++count,total:ALL.length});}port.postMessage({done:true,version:'1.1.0'});}catch(err){port.postMessage({done:true,error:err.message});}})());});
