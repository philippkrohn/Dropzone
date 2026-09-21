/** Framework-free quiz logic; reusable for any faction and detachment. */
export const STORE_PREFIX = 'pkstratagems:quiz:v1:';
export const safeId = value => typeof value === 'string' && /^[a-z0-9][a-z0-9-]{1,100}$/.test(value);
export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function validateQuiz(quiz) {
  if (!quiz || quiz.schemaVersion !== 1 || !safeId(quiz.id)) throw new Error('Ungültiges Quizformat.');
  for (const key of ['title','faction','detachment','description','revision','rulesBasis']) if (typeof quiz[key] !== 'string' || !quiz[key].trim()) throw new Error(`Quizfeld fehlt: ${key}`);
  if (!['easy','medium','hard'].includes(quiz.difficulty)) throw new Error('Unbekannte Schwierigkeit.');
  if (!Array.isArray(quiz.tags) || !quiz.tags.every(t=>typeof t === 'string')) throw new Error('Ungültige Themen.');
  if (!Array.isArray(quiz.questions) || !quiz.questions.length || quiz.questions.length>100) throw new Error('Ungültige Fragenzahl.');
  if (quiz.questionCount !== quiz.questions.length) throw new Error('Fragenzahl stimmt nicht überein.');
  if (!Array.isArray(quiz.sources) || !quiz.sources.length) throw new Error('Quellen fehlen.');
  const sourceIds = new Set(quiz.sources.map(s=>s.id));
  if(sourceIds.size !== quiz.sources.length) throw new Error('Doppelte Quellenkennung.');
  const ids = new Set();
  for (const q of quiz.questions) {
    if (!safeId(q.id) || ids.has(q.id) || q.type !== 'single-choice') throw new Error('Ungültige oder doppelte Frage.');
    ids.add(q.id);
    if (!q.prompt || !q.explanation || !Array.isArray(q.options) || q.options.length<2 || q.options.length>8) throw new Error('Unvollständige Frage.');
    const options=new Set(q.options.map(o=>o.id));
    if(options.size!==q.options.length || !q.options.every(o=>safeId(o.id)&&typeof o.text==='string'&&o.text.trim()) || !options.has(q.correctOptionId)) throw new Error('Ungültige Antworten.');
    if(!Array.isArray(q.sourceIds)||!q.sourceIds.length||!q.sourceIds.every(s=>sourceIds.has(s))) throw new Error('Frage ohne gültige Quelle.');
  }
  return quiz;
}
export function validateCatalog(catalog) {
  if(catalog?.schemaVersion!==1 || !Array.isArray(catalog.quizzes)) throw new Error('Quizkatalog nicht lesbar.');
  const ids=new Set();
  for(const q of catalog.quizzes) {
    if(!safeId(q.id)||ids.has(q.id)||q.file!==`${q.id}.json`) throw new Error('Ungültiger Quizpfad.');
    ids.add(q.id);
    for(const key of ['title','faction','detachment','difficulty','description']) if(typeof q[key]!=='string') throw new Error('Katalogeintrag unvollständig.');
    if(!Array.isArray(q.tags)||!Number.isInteger(q.questionCount)||q.questionCount<1) throw new Error('Katalogeintrag unvollständig.');
  }
  return catalog;
}
export function filterQuizzes(quizzes, {search='',faction='',detachment='',difficulty=''}={}) {
  const needle=search.toLocaleLowerCase('de').trim();
  return quizzes.filter(q=>(!faction||q.faction===faction)&&(!detachment||q.detachment===detachment)&&(!difficulty||q.difficulty===difficulty)&&(!needle||[q.title,q.description,q.faction,q.detachment,...q.tags].join(' ').toLocaleLowerCase('de').includes(needle)));
}
export function grade(quiz, answers={}, ids=quiz.questions.map(q=>q.id)) {
  const wanted=new Set(ids);
  const rows=quiz.questions.filter(q=>wanted.has(q.id)).map(q=>{
    const choice=q.options.some(o=>o.id===answers[q.id])?answers[q.id]:null;
    return {id:q.id,selected:choice,correct:choice===q.correctOptionId,answered:choice!==null};
  });
  const correct=rows.filter(q=>q.correct).length;
  return {total:rows.length,answered:rows.filter(q=>q.answered).length,correct,percent:rows.length?Math.round(correct/rows.length*100):0,rows,wrongIds:rows.filter(q=>!q.correct).map(q=>q.id)};
}
export function storageKey(quiz){return STORE_PREFIX+quiz.id+':'+quiz.revision;}
export function newAttempt(quiz, questionIds=quiz.questions.map(q=>q.id)) {return {quizId:quiz.id,revision:quiz.revision,questionIds:[...questionIds],answers:{},position:0,submitted:false};}
export function restoreAttempt(quiz,raw) {
  try {
    const x=JSON.parse(raw);
    if(x.quizId!==quiz.id || x.revision!==quiz.revision || !Array.isArray(x.questionIds)||!x.questionIds.length||new Set(x.questionIds).size!==x.questionIds.length) return null;
    if(!x.questionIds.every(id=>quiz.questions.some(q=>q.id===id))) return null;
    const a=newAttempt(quiz,x.questionIds);
    for(const q of quiz.questions) if(q.options.some(o=>o.id===x.answers?.[q.id])) a.answers[q.id]=x.answers[q.id];
    a.position=Number.isInteger(x.position)?Math.max(0,Math.min(x.position,a.questionIds.length-1)):0;
    a.submitted=x.submitted===true&&grade(quiz,a.answers,a.questionIds).answered===a.questionIds.length;
    return a;
  } catch{return null;}
}
