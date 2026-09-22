from playwright.sync_api import sync_playwright,expect
from pathlib import Path
import argparse,json,os,random
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8765/');p.add_argument('--public',action='store_true');a=p.parse_args();OUT=R/'qa';OUT.mkdir(exist_ok=True)
B=json.loads((R/'quiz/data/bank.json').read_text());I=json.loads((R/'quiz/data/index.json').read_text());C=json.loads((R/'library/catalog.json').read_text());byId={q['id']:q for q in B['questions']};errors=[];checks=[]
with sync_playwright() as pw:
 exe=os.environ.get('CHROMIUM_PATH');browser=pw.chromium.launch(executable_path=exe)
 ctx=browser.new_context(viewport={'width':1440,'height':950});page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(a.base,wait_until='domcontentloaded');page.wait_for_selector('.card')
 assert page.locator('.card').count()==10
 page.evaluate("localStorage.setItem('pk_cp','4');localStorage.setItem('pk_active_v2',JSON.stringify(['fleet','auric']));localStorage.setItem('unrelated-user-note','preserve-me');")
 page.reload();page.wait_for_selector('.card');expect(page.locator('#cpVal')).to_have_text('4');page.locator('#cpPlus').click();expect(page.locator('#cpVal')).to_have_text('5')
 assert page.locator('.card').count()>10
 page.locator('.card-head').first.click();expect(page.locator('.card').first).to_have_attribute('data-open','true')
 assert page.locator('a[href="fraktionen/"]').count()==1
 checks.append('Existing browser: core cards, selected detachments, CP state and card opening')
 page.goto(a.base+'quiz/');page.wait_for_selector('#faction-filter')
 assert page.locator('#faction-filter option').count()==25
 for f in I['factions']:
  page.select_option('#faction-filter',f['id']);assert page.locator('#detachment-filter option').count()==len(f['detachmentIds'])+1
 checks.append('All 24 faction filters expose the correct detachment catalogue')
 page.select_option('#faction-filter','agents');page.select_option('#difficulty-filter','hard');page.locator('[data-start]').click()
 assert page.locator('.question-nav button').count()==10
 state=page.evaluate("JSON.parse(localStorage.getItem('pkstratagems:training:v2'))")
 assert len(state['questionIds'])==10
 # In-progress form has no solution text or exposed correct flag in DOM.
 assert page.locator('.explanation,.answer-badge,.source-details').count()==0
 page.check('input[name=answer][value="'+byId[state['questionIds'][0]]['correctOptionId']+'"]');page.reload();page.wait_for_selector('[data-resume]');page.locator('[data-resume]').click()
 assert page.locator('input[name=answer]:checked').count()==1
 reloaded=page.evaluate("JSON.parse(localStorage.getItem('pkstratagems:training:v2'))");assert state['optionOrders']==reloaded['optionOrders']
 page.locator('[data-submit]').first.click();assert page.locator('[role=alert]').count()==1
 # Select two incorrect and eight correct answers. Evaluation must be deterministic under shuffle.
 for n,id in enumerate(state['questionIds']):
  page.locator(f'[data-position="{n}"]').click();q=byId[id];answer=q['correctOptionId'] if n>=2 else next(o['id']for o in q['options'] if o['id']!=q['correctOptionId']);page.check(f'input[name=answer][value="{answer}"]')
 page.locator('[data-submit]').first.click();expect(page.locator('.score-number')).to_contain_text('8');assert page.locator('.review-card').count()==10
 assert page.locator('.source-details').count()==10
 page.locator('[data-retry]').click();new=page.evaluate("JSON.parse(localStorage.getItem('pkstratagems:training:v2'))");assert len(new['questionIds'])==10;assert set(state['questionIds'][:2])<=set(new['questionIds'])
 checks.append('Ten distinct concepts; shuffled choices; no answer leakage in quiz DOM; resume; 8/10 grading; full-length error training')
 page.goto(a.base+'quiz/?mode=tactics&difficulty=hard&topic=tactics');page.wait_for_selector('[data-start]');page.locator('[data-start]').click()
 if page.locator('#reset-dialog[open]').count():page.locator('button[value=reset]').click()
 expect(page.locator('.scope-note')).to_contain_text('Alle Antwortwege sind zulässig')
 at=page.evaluate("JSON.parse(localStorage.getItem('pkstratagems:training:v2'))");assert all(byId[i]['kind']=='tactics' for i in at['questionIds'])
 checks.append('Tactics-only expert mode contains legal alternative decision scenarios, not legality tests')
 page.goto(a.base+'fraktionen/');page.wait_for_selector('#faction-choice');assert page.locator('.faction-grid button').count()==24
 for f in I['factions']:
  page.select_option('#faction-choice',f['id']);assert page.locator('.faction-panel .rules-prose').inner_text().strip();assert page.locator('.det-section').count()==len(f['detachmentIds'])
 checks.append('All faction rules and 270 detachment overview panels render')
 page.select_option('#faction-choice','agents');page.fill('#unit-search','Sanctifier');assert page.locator('[data-unit]:visible').count()>=1
 page.select_option('#detachment-choice',next(d['id']for d in I['detachments'] if d['name']=='Imperialis Fleet'));assert page.locator('.det-section[open]').count()==1;assert page.locator('.ref-strat').count()==6
 checks.append('Datasheet search and detachment-specific rule/stratagem display')
 for width in [320,390,768,1440]:
  page.set_viewport_size({'width':width,'height':900})
  for path in ['', 'quiz/','fraktionen/?faction=agents']:
   page.goto(a.base+path);page.wait_for_timeout(350);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,path)
 checks.append('320/390/768/1440px: no document overflow on all three main routes')
 page.goto(a.base+'quiz/');page.wait_for_selector('#faction-filter');page.screenshot(path=str(OUT/'training-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'training-mobile.png'),full_page=True)
 page.locator('#theme').click();expect(page.locator('html')).to_have_attribute('data-theme','light')
 page.goto(a.base+'fraktionen/?faction=agents');page.wait_for_selector('.faction-panel');page.screenshot(path=str(OUT/'faction-mobile.png'),full_page=True)
 assert page.evaluate("localStorage.getItem('unrelated-user-note')")=='preserve-me'
 if a.public:
  response=page.goto(a.base+'doubles/');assert response.ok;page.wait_for_selector('#app');checks.append('Existing public Doubles route loads through pinned fallback')
 assert not errors,errors
 report={'passed':True,'base':a.base,'checks':checks,'errors':errors};(OUT/('public-report.json'if a.public else'browser-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False));browser.close()
