import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {resolveCase,parseSelection,selectionQuery,escapeHtml,validateNotesFile,STORAGE} from '../core.mjs';
const cases=JSON.parse(readFileSync(new URL('../data/cases.json',import.meta.url)));
for(const c of cases)for(const role of ['attacker','defender'])for(const turn of ['unknown','first','second'])test(`${c.code} ${role} ${turn}`,()=>{
 const s=parseSelection(`?case=${c.code}&role=${role}&turn=${turn}`,cases);
 assert.equal(s.error,'');assert.equal(resolveCase(cases,s).code,c.code);assert.equal(s.role,role);assert.equal(s.turn,turn);
 assert.deepEqual(parseSelection(selectionQuery(s,c),cases),s);
});
test('missing game-three assignment is never guessed',()=>assert.equal(resolveCase(cases,{game:3,opp:'disruption',own:''}),null));
test('game one and two force the approved disposition',()=>{assert.equal(resolveCase(cases,{game:1,opp:'take-and-hold',own:'priority-assets'}).code,'A01');assert.equal(resolveCase(cases,{game:2,opp:'take-and-hold',own:'reconnaissance'}).code,'B01');});
for(const q of ['?case=NOPE','?game=9','?game=3&own=purge-the-foe','?opp=bad','?role=bad','?turn=bad','?view=bad'])test(`reject ${q}`,()=>assert.ok(parseSelection(q,cases).error));
test('text is HTML escaped',()=>assert.equal(escapeHtml('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;'));
test('notes round trip',()=>{const v={app:'Dropzone',version:1,records:[{key:STORAGE+'game1:A01',value:{note0:'<safe>',check0:true}}]};assert.deepEqual(validateNotesFile(v),v.records);});
test('unrelated storage is rejected',()=>assert.throws(()=>validateNotesFile({app:'Dropzone',version:1,records:[{key:'other-app',value:{}}]})));
test('unexpected keys are rejected',()=>assert.throws(()=>validateNotesFile({app:'Dropzone',version:1,records:[{key:STORAGE+'game1:A01',value:{token:'bad'}}]})));
test('share URL contains no notes',()=>assert.ok(!selectionQuery({game:1,role:'defender',turn:'first',view:'notes',note0:'PRIVATE'},cases[0]).includes('PRIVATE')));
