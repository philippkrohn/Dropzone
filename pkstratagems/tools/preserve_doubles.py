"""Preserve the actual existing inline Doubles application, not the separate Pages app.
Copy bytes only, including the linked original PDF; no strategy or PDF changes.
"""
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urljoin,quote
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
BASE='https://6ab1939ae68f1a942996df56--pkstratagems.netlify.app/doubles/'
OUT=ROOT/'netlify-site/public/doubles';OUT.mkdir(parents=True,exist_ok=True)
def fetch(path):
 assert not path.startswith(('/', 'http')) and '..' not in path.split('/')
 with urlopen(Request(BASE+quote(path,safe='/._-'),headers={'User-Agent':'PK-Stratagems preservation check'}),timeout=60) as response:raw=response.read()
 assert raw,path+' is empty'
 return raw
index=fetch('');text=index.decode();manifest={'baseline':BASE,'files':{}}
def store(path,raw):
 dst=OUT/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
 manifest['files'][path]=hashlib.sha256(raw).hexdigest()
store('index.html',index)
# Source paths are discovered from the actual inline load() function.
jsonpaths=set(re.findall(r'[\"\'](daten/[^\"\']+\.json)[\"\']',text))
assert len(jsonpaths)==4,'Unexpected existing Doubles data manifest.'
assets=set(re.findall(r'[\"\']((?:assets|referenz)/[^\"\'${}]+\.(?:png|webp|jpg|jpeg|pdf))[\"\']',text))
def walk(value):
 if isinstance(value,dict):
  for v in value.values():walk(v)
 elif isinstance(value,list):
  for v in value:walk(v)
 elif isinstance(value,str) and re.fullmatch(r'(?:assets|referenz)/[^\n<>]+\.(?:png|webp|jpg|jpeg|pdf)',value):assets.add(value)
for path in sorted(jsonpaths):
 raw=fetch(path);store(path,raw);walk(json.loads(raw))
assert assets,'No original Doubles images discovered.'
def preserve(path):return path,fetch(path)
with ThreadPoolExecutor(max_workers=4) as pool:
 for path,raw in pool.map(preserve,sorted(assets)):store(path,raw)
(ROOT/'qa').mkdir(exist_ok=True)
(ROOT/'qa/doubles-preservation.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Preserved',len(manifest['files']),'original Doubles files byte-for-byte, including all declared assets; no nested proxy.')
