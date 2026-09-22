"""Collect public rule-source pages for review; this does NOT publish their contents."""
from pathlib import Path
from urllib.parse import urljoin,urlparse
from urllib.request import urlopen,Request
from bs4 import BeautifulSoup
import json,re,time,hashlib,concurrent.futures
OUT=Path('training-sources');OUT.mkdir(exist_ok=True)
BASE='https://wahapedia.ru';reports=[]
def fetch(url,path):
 try:
  req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PK-Stratagems rules review)'})
  with urlopen(req,timeout=45) as r:raw=r.read();final=r.url
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  reports.append({'path':str(path.relative_to(OUT)),'url':final,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  return BeautifulSoup(raw,'html.parser')
 except Exception as e:reports.append({'url':url,'error':str(e)});return None
nav=fetch(BASE+'/wh40k11ed/nav.html',OUT/'nav.html')
assert nav is not None
links={urljoin(BASE,a['href']).rstrip('/')+'/':a.get_text(' ',strip=True) for a in nav.select('a[href]') if re.fullmatch(r'/wh40k11ed/factions/[^/]+/?',a['href'])}
assert links, 'No discovered factions; no guessed catalogue.'
print('Discovered factions',json.dumps(links),flush=True)
def faction(item):
 url,name=item;slug=urlparse(url).path.split('/')[3]
 soup=fetch(url,OUT/'factions'/(slug+'.html'))
 if soup is None:return
 node=soup.find(id='siteNav')
 if node and node.get('data-armylist-file'):
  armyurl=urljoin(BASE,node['data-armylist-file']);fetch(armyurl,OUT/'armylists'/(slug+'.html'))
 time.sleep(1)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(faction,links.items()))
(OUT/'catalogue.json').write_text(json.dumps(links,ensure_ascii=False,indent=2))
(OUT/'fetch-report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
print('Retrieved',len([r for r in reports if 'error' not in r]),'resources;',len([r for r in reports if 'error' in r]),'errors')
