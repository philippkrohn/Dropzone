/** Add a valid quiz JSON file to quiz/data/, then run this script. */
import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';import {validateQuiz} from '../quiz/core.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','quiz','data');
const quizzes=[];
for(const file of (await fs.readdir(root)).sort()){
 if(!file.endsWith('.json')||file==='index.json'||file==='schema.json')continue;
 const q=validateQuiz(JSON.parse(await fs.readFile(path.join(root,file),'utf8')));
 if(file!==q.id+'.json')throw new Error('Dateiname muss der Quiz-ID entsprechen: '+file);
 const entry=Object.fromEntries(['id','title','faction','detachment','difficulty','questionCount','estimatedMinutes','description','tags'].map(k=>[k,q[k]]));
 quizzes.push({...entry,file});
}
await fs.writeFile(path.join(root,'index.json'),JSON.stringify({schemaVersion:1,quizzes},null,2)+'\n');
console.log(`${quizzes.length} Quizze im Katalog.`);
