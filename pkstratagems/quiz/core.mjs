/** Generic, versioned ten-question training engine. No player-specific assumptions. */
export const VERSION='2.0.0';
export const SESSION_LENGTH=10;
export const STORAGE_KEY='pkstratagems:training:v2';
export const LEVELS=['easy','medium','hard'];
export function h(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
export function shuffle(values,random=Math.random){const out=[...values];for(let i=out.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[out[i],out[j]]=[out[j],out[i]];}return out;}
export function normalConfig(input={}){return {faction:input.faction||'',detachment:input.detachment||'',difficulty:LEVELS.includes(input.difficulty)?input.difficulty:'medium',mode:['rules','tactics','mixed'].includes(input.mode)?input.mode:'mixed',topic:input.topic||''};}
export function validateBank(bank){
 if(bank.schemaVersion!==2||bank.sessionLength!==10||!Array.isArray(bank.questions))throw Error('Unbekannter Fragenpool.');
 const ids=new Set();for(const q of bank.questions){
  if(!q.id||ids.has(q.id)||!q.conceptId||!LEVELS.includes(q.difficulty)||!['rules','tactics'].includes(q.kind)||typeof q.prompt!=='string'||!Array.isArray(q.options)||q.options.length!==3)throw Error('Ungültige Frage: '+q.id);
  ids.add(q.id);const os=q.options.map(o=>o.id);if(new Set(os).size!==3||!os.includes(q.correctOptionId)||q.options.some(o=>typeof o.text!=='string')||new Set(q.options.map(o=>o.text)).size!==3||!q.explanation||!q.sources?.length)throw Error('Ungültige Antworten/Quellen: '+q.id);
  if(q.kind==='tactics'&&q.topic!=='tactics')throw Error('Taktik ist getrennt von Regelzulässigkeit.');
 }return bank;
}
export function poolFor(bank,input){const c=normalConfig(input);return bank.questions.filter(q=>{
 if(q.difficulty!==c.difficulty)return false;
 if(c.mode==='tactics'&&q.kind!=='tactics'||c.mode==='rules'&&q.kind!=='rules')return false;
 if(c.topic&&q.topic!==c.topic)return false;
 if(c.mode==='tactics')return true; // Explicitly labelled cross-faction tactical decision training.
 if(c.faction&&q.faction&&q.faction!==c.faction)return false;
 if(c.detachment&&q.detachment&&q.detachment!==c.detachment)return false;
 return true;
});}
export function conceptCount(pool){return new Set(pool.map(q=>q.conceptId)).size;}
export function makeAttempt(bank,config,{random=Math.random,priorityIds=[]}={}){
 const c=normalConfig(config),pool=poolFor(bank,c);if(conceptCount(pool)<SESSION_LENGTH)throw Error('Für diese Auswahl sind weniger als zehn unterschiedliche Fragekonzepte verfügbar. Bitte Thema oder Detachment erweitern.');
 const chosen=[],used=new Set();function take(candidates,n){for(const q of shuffle(candidates,random)){if(chosen.length>=SESSION_LENGTH||n<=0)break;if(used.has(q.conceptId))continue;chosen.push(q);used.add(q.conceptId);n--;}}
 // Wrong-answer training prioritizes mistakes but remains a full ten-question session.
 take(pool.filter(q=>priorityIds.includes(q.id)),10);
 if(!c.topic){
  if(c.mode==='mixed')take(pool.filter(q=>q.kind==='tactics'),2);
  if(c.mode!=='tactics'){
   take(pool.filter(q=>q.topic==='stratagem'&&(!c.detachment||q.detachment===c.detachment)),3);
   take(pool.filter(q=>q.topic==='detachment'&&(!c.detachment||q.detachment===c.detachment)),1);
   take(pool.filter(q=>q.topic==='faction'&&(!c.faction||q.faction===c.faction)),1);
   take(pool.filter(q=>q.topic==='datasheet'&&(!c.faction||q.faction===c.faction)),2);
   take(pool.filter(q=>q.topic==='core'),1);
  }
 }
 // Prefer selected faction material before filling with visibly labelled universal rules.
 take(pool.filter(q=>q.faction&&(!c.faction||q.faction===c.faction)),10);
 take(pool,10);if(chosen.length!==10)throw Error('Der Pool enthält zu wenig unterschiedliche Konzepte.');
 const questions=shuffle(chosen,random);return {schemaVersion:2,bankVersion:bank.version,config:c,questionIds:questions.map(q=>q.id),optionOrders:Object.fromEntries(questions.map(q=>[q.id,shuffle(q.options.map(o=>o.id),random)])),answers:{},position:0,submitted:false,createdAt:new Date().toISOString(),retry:priorityIds.length>0};
}
export function grade(bank,attempt){const byId=new Map(bank.questions.map(q=>[q.id,q]));const rows=attempt.questionIds.map(id=>{const q=byId.get(id);return {id,selected:attempt.answers[id]??null,answered:!!attempt.answers[id],correct:attempt.answers[id]===q.correctOptionId,topic:q.topic};});const correct=rows.filter(r=>r.correct).length;return {rows,total:rows.length,answered:rows.filter(r=>r.answered).length,correct,percent:Math.round(correct*100/rows.length),wrongIds:rows.filter(r=>!r.correct).map(r=>r.id)};}
export function restoreAttempt(bank,raw){try{const a=typeof raw==='string'?JSON.parse(raw):raw;if(!a||a.schemaVersion!==2||a.bankVersion!==bank.version||a.questionIds?.length!==10||new Set(a.questionIds).size!==10)return null;
 const byId=new Map(bank.questions.map(q=>[q.id,q]));const allowed=new Set(poolFor(bank,a.config).map(q=>q.id));const concepts=new Set();for(const id of a.questionIds){const q=byId.get(id);if(!q||!allowed.has(id)||concepts.has(q.conceptId))return null;concepts.add(q.conceptId);const order=a.optionOrders?.[id];if(!order||order.length!==3||new Set(order).size!==3||order.some(x=>!q.options.some(o=>o.id===x)))return null;if(a.answers?.[id]&&!order.includes(a.answers[id]))return null;}
 if(!Number.isInteger(a.position)||a.position<0||a.position>9||typeof a.submitted!=='boolean')return null;if(a.submitted&&Object.keys(a.answers||{}).length!==10)return null;return a;
 }catch{return null;}}
export function configFromURL(search){const p=new URLSearchParams(search);return normalConfig({faction:p.get('faction'),detachment:p.get('detachment'),difficulty:p.get('difficulty'),mode:p.get('mode'),topic:p.get('topic')});}
export function configURL(config,base){const u=new URL(base);u.search='';for(const [k,v] of Object.entries(normalConfig(config)))if(v)u.searchParams.set(k,v);u.hash='';return u.href;}
