"""Functional and responsive quiz checks; no PDF creation or game-rule changes."""
import argparse,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8768/');args=p.parse_args()
OUT=ROOT/'qa';OUT.mkdir(exist_ok=True)
quiz=json.loads((ROOT/'quiz/data/imperial-agents-imperialis-fleet-grundlagen.json').read_text())
report={'base':args.base,'checks':[],'errors':[]}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium') if Path(os.environ.get('CHROMIUM_PATH','/usr/bin/chromium')).exists() else None)
 ctx=browser.new_context(viewport={'width':1280,'height':920},reduced_motion='reduce')
 page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
 def start():
  page.goto(args.base+'quiz/?quiz='+quiz['id']);page.locator('[data-start]').click()
 page.goto(args.base)
 page.wait_for_selector('#cpPlus');oldcp=int(page.locator('#cpVal').inner_text());page.locator('#cpPlus').click();expect(page.locator('#cpVal')).to_have_text(str(oldcp+1))
 assert page.locator('.section-links .quiz-link').count()==1
 page.screenshot(path=str(OUT/'pk-home.png'),full_page=False)
 page.locator('.section-links .quiz-link').click();expect(page.locator('.quiz-card')).to_have_count(1)
 page.fill('#quiz-search','nothingzz');expect(page.locator('.quiz-card')).to_have_count(0)
 page.locator('[data-clear-filters]').click();expect(page.locator('.quiz-card')).to_have_count(1)
 page.select_option('#difficulty-filter','hard');expect(page.locator('.quiz-card')).to_have_count(0)
 page.select_option('#difficulty-filter','medium');expect(page.locator('.quiz-card')).to_have_count(1)
 page.select_option('#faction-filter','Imperial Agents');page.select_option('#detachment-filter','Imperialis Fleet')
 page.locator('[data-open]').click();page.locator('[data-start]').click();assert page.locator('.explanation').count()==0
 page.locator('[data-submit]').click();expect(page.locator('[role=alert]')).to_contain_text('8 Fragen offen')
 page.locator('input[name=answer]').first.check();expect(page.locator('#progress-label')).to_have_text('1 von 8 beantwortet')
 page.reload();page.locator('[data-start]').click();expect(page.locator('input[name=answer]').first).to_be_checked()
 report['checks'].append('Existing CP tracker and navigation; catalog filters; no answer leak before grading; incomplete submission blocked; local resume.')
 for i,q in enumerate(quiz['questions']):
  page.locator(f'[data-position="{i}"]').click();page.locator(f'input[value="{q["correctOptionId"]}"]').check()
 page.locator('[data-submit]').click();expect(page.locator('.score-number')).to_contain_text('8');assert page.locator('.review-card').count()==8
 assert page.locator('.review-state.wrong').count()==0;assert page.locator('.explanation').count()==8
 page.locator('.sources summary').first.click();expect(page.locator('.sources').first).to_contain_text('Faction Pack')
 page.evaluate("localStorage.setItem('untouched-existing-setting','keep-me')")
 page.locator('[data-reset]').first.click();page.locator('#reset-dialog button[value=cancel]').click();assert page.locator('.review-card').count()==8
 page.locator('[data-reset]').first.click();page.locator('#reset-dialog button[value=reset]').click()
 for i,q in enumerate(quiz['questions']):
  page.locator(f'[data-position="{i}"]').click();choice=q['correctOptionId'] if i else next(o['id'] for o in q['options'] if o['id']!=q['correctOptionId']);page.locator(f'input[value="{choice}"]').check()
 page.locator('[data-submit]').click();assert page.locator('.review-state.wrong').count()==1
 page.locator('[data-retry-wrong]').click();assert page.locator('.question-nav button').count()==1
 page.locator(f'input[value="{quiz["questions"][0]["correctOptionId"]}"]').check();page.locator('[data-submit]').click();expect(page.locator('.result-hero')).to_contain_text('100 %')
 assert page.evaluate("localStorage.getItem('untouched-existing-setting')")=='keep-me'
 assert 'answers=' not in page.url
 report['checks'].append('8/8 grading with explanations/sources; cancel-safe reset; 7/8 and wrong-only retry; isolated storage; share URL contains no answers.')
 for width in [320,390,768,1280]:
  page.set_viewport_size({'width':width,'height':844});page.goto(args.base+'quiz/');page.wait_for_selector('.quiz-card');assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
  start()
  if page.locator('.review-card').count():
   page.locator('[data-reset]').first.click();page.locator('#reset-dialog button[value=reset]').click()
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
  page.screenshot(path=str(OUT/f'quiz-{width}.png'),full_page=True)
  page.goto(args.base);page.wait_for_selector('.quiz-link');assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),('home',width)
 report['checks'].append('Home, catalog and question views at 320/390/768/1280px with no page-level horizontal overflow.')
 page.goto(args.base+'quiz/?quiz=not-an-existing-quiz');expect(page.locator('#main')).to_contain_text('Quiz nicht gefunden')
 page.goto(args.base+'quiz/');page.wait_for_selector('.quiz-card');page.locator('#theme').click();expect(page.locator('html')).to_have_attribute('data-theme','light')
 page.screenshot(path=str(OUT/'quiz-catalog-light.png'),full_page=True)
 assert not report['errors'],report['errors'];report['passed']=True
 (OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2));browser.close()
