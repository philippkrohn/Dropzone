"""Mirror only resources declared by the existing Doubles app, byte-for-byte.
Avoids a Netlify proxy-to-proxy chain; no PDF or strategy content is modified.
"""
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urljoin,urlparse
from concurrent.futures import ThreadPoolExecutor
import ast,hashlib,json,re
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
BASE='https://6ab1939ae68f1a942996df56--pkstratagems.netlify.app/doubles/'
OUT=ROOT/'netlify-site/public/doubles';OUT.mkdir(parents=True,exist_ok=True)
def fetch(path):
 url=urljoin(BASE,path)
 assert url.startswith(BASE) and '..' not in path.split('/')
 with urlopen(Request(url,headers={'User-Agent':'PK-Stratagems preservation check'}),timeout=60) as response:raw=response.read()
 assert raw,path+' is empty'
 return raw
index=fetch('');soup=BeautifulSoup(index,'html.parser')
paths=set()
for tag in soup.select('script[src],link[href]'):
 value=tag.get('src',tag.get('href',''))
 if value.startswith(('./','data/','assets/')):paths.add(value.removeprefix('./'))
assert 'app.mjs' in paths
app=fetch('app.mjs').decode()
for pattern in [r"from\s*['\"](\./[^'\"]+)['\"]",r"register\(['\"](\./[^'\"]+)['\"]"]:
 paths.update(p.removeprefix('./') for p in re.findall(pattern,app))
assert 'sw.js' in paths
sw=fetch('sw.js').decode()
def declared_array(name):
 match=re.search(r'const\s+'+name+r'\s*=\s*(\[[^;]+\])\s*;',sw)
 assert match,'Existing offline manifest '+name+' not recognized'
 return ast.literal_eval(match.group(1))
for p in declared_array('CORE'):
 if p not in ['./','index.html']:paths.add(p.removeprefix('./'))
# These names come directly from the existing app's documented offline manifest.
assert 'assets/layouts/board-${p}.webp' in sw and 'assets/layouts/page-${p}.webp' in sw
for p in declared_array('PAGES'):
 assert isinstance(p,int)
 for kind in ['board','page']:paths.add(f'assets/layouts/{kind}-{p}.webp')
assert 40<len(paths)<100
manifest={'baseline':BASE,'files':{'index.html':hashlib.sha256(index).hexdigest()}}
(OUT/'index.html').write_bytes(index)
def preserve(path):
 data=fetch(path);dst=OUT/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
 return path,hashlib.sha256(data).hexdigest()
with ThreadPoolExecutor(max_workers=4) as pool:
 for path,digest in pool.map(preserve,sorted(paths)):manifest['files'][path]=digest
(ROOT/'qa').mkdir(exist_ok=True);(ROOT/'qa/doubles-preservation.json').write_text(json.dumps(manifest,indent=2))
print('Preserved',len(manifest['files']),'existing Doubles resources byte-for-byte; no proxy chain needed.')
