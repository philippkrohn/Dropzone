"""Transfer the approved static preview; never rebuild or edit game rules.
Authorization is encrypted for one ephemeral Actions run and one exact bundle.
"""
from pathlib import Path
import base64, concurrent.futures, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request, urllib.error, urllib.parse, zipfile
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT=Path(__file__).resolve().parents[1]; PK=ROOT/'pkstratagems'; OUT=ROOT/'delivery'; SITE=OUT/'site'; EVIDENCE=OUT/'evidence'; AUTH=OUT/'authorization'; PACKAGES=OUT/'packages'
PREVIEW='https://6ab273d19010e1b07416775d--pkstratagems-vorschau.netlify.app/'
PRODUCTION='https://pkstratagems.netlify.app/'
BASELINE='https://6ab1939ae68f1a942996df56--pkstratagems.netlify.app/'
SITE_ID='a9b698e5-0f1d-4f39-b84d-ce52c91179a7'
BRANCH='fix/pk-preview-publication-2026-09-27'; REPO='philippkrohn/Dropzone'
RUN=os.environ['GITHUB_RUN_ID']; ATTEMPT=os.environ['GITHUB_RUN_ATTEMPT']
KEY=Path(os.environ['RUNNER_TEMP'])/('pk-promotion-'+RUN+'-'+ATTEMPT+'.pem')
CONFIG='[build]\n  publish = "."\n  command = "test -f index.html && test -f quiz/index.html && test -f fraktionen/index.html && test -f doubles/index.html"\n'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def get(url,attempts=5):
 for n in range(attempts):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'PK-Stratagems approved-preview transfer','Cache-Control':'no-cache'}),timeout=40) as r:return r.read()
  except urllib.error.HTTPError as e:
   if e.code<500 and e.code!=429:raise RuntimeError('Public source HTTP '+str(e.code)+' at '+url.split('?')[0]) from None
  except (OSError,TimeoutError):pass
  if n+1<attempts:time.sleep(min(2**n,12))
 raise RuntimeError('Public source unavailable after retries: '+url.split('?')[0])
def safe_path(path):
 assert path and not path.startswith('/') and not any(s in ['..',''] for s in path.split('/')),path
 return path
def web(base,path):return base+urllib.parse.quote(safe_path(path),safe='/._-')
def store(path,raw):
 p=SITE/safe_path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
def records():return {p.relative_to(SITE).as_posix():sha(p.read_bytes()) for p in sorted(SITE.rglob('*')) if p.is_file()}
def prepare():
 for p in [EVIDENCE,AUTH,PACKAGES]:p.mkdir(parents=True,exist_ok=True)
 subprocess.run([sys.executable,str(PK/'tools/assemble_v2.py')],check=True,cwd=ROOT)
 shutil.copytree(PK/'netlify-site/public',SITE)
 # The tracked source supplies the file inventory, but bytes must match the approved preview.
 copied={}
 def verify_file(p):
  path=p.relative_to(SITE).as_posix()
  raw=get(web(PREVIEW,path));assert raw==p.read_bytes(),'Approved preview differs from source: '+path
  return path,sha(raw)
 paths=[p for p in SITE.rglob('*') if p.is_file() and p.name not in ['_redirects','_headers','netlify.toml']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for path,digest in pool.map(verify_file,paths):copied[path]=digest
 # Discover all actual inline Doubles dependencies rather than copying the separate Pages app.
 index=get(PREVIEW+'doubles/');text=index.decode();store('doubles/index.html',index)
 jsonpaths=set(re.findall(r'[\"\'](daten/[^\"\']+\.json)[\"\']',text))
 assert len(jsonpaths)==4,'Unexpected Doubles dependency list'
 assets=set(re.findall(r'[\"\']((?:assets|referenz)/[^\"\'${}]+\.(?:png|webp|jpg|jpeg|pdf))[\"\']',text))
 def walk(v):
  if isinstance(v,dict):
   for x in v.values():walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
  elif isinstance(v,str) and re.fullmatch(r'(?:assets|referenz)/[^\n<>]+\.(?:png|webp|jpg|jpeg|pdf)',v):assets.add(v)
 for path in sorted(jsonpaths):
  raw=get(web(PREVIEW+'doubles/',path));store('doubles/'+path,raw);walk(json.loads(raw))
 assert assets,'No Doubles assets'
 def retrieve(path):return path,get(web(PREVIEW+'doubles/',path))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for path,raw in pool.map(retrieve,sorted(assets)):store('doubles/'+path,raw)
 # Static output at the root must be published from '.', not a non-existent 'public'.
 (SITE/'netlify.toml').write_text(CONFIG)
 # Preserve the existing fallback for historical URLs, outside the new directly served files.
 assert (SITE/'_redirects').read_text().strip()=='/* '+BASELINE.rstrip('/')+'/:splat 200'
 assert (SITE/'index.html').is_file() and (SITE/'quiz/index.html').is_file() and (SITE/'doubles/index.html').is_file()
 baseline=get(BASELINE);assert get(PRODUCTION)==baseline,'Production changed: do not overwrite.'
 (EVIDENCE/'baseline-root.sha256').write_text(sha(baseline))
 files=records();(EVIDENCE/'files.json').write_text(json.dumps(files,ensure_ascii=False,indent=2))
 (EVIDENCE/'assembly.json').write_text(json.dumps({'preview':PREVIEW,'target':SITE_ID,'matchingNewFiles':len(copied),'doublesFiles':len([x for x in files if x.startswith('doubles/')]),'files':len(files),'publish':'.','baselineRootSHA256':sha(baseline)},indent=2))
 # Private key stays outside all artifact paths, and is deleted before publication.
 private=rsa.generate_private_key(public_exponent=65537,key_size=3072)
 KEY.write_bytes(private.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));KEY.chmod(0o600)
 public=private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
 (AUTH/'public.pem').write_bytes(public)
 archive=PACKAGES/'PK_Stratagems_korrigierter_Upload.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for path in files:z.write(SITE/path,'PK_Stratagems/'+path)
 metadata={'runId':RUN,'runAttempt':ATTEMPT,'keyId':sha(public),'siteId':SITE_ID,'branch':BRANCH,'preview':PREVIEW,'bundleSHA256':sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode()),'archiveSHA256':sha(archive.read_bytes())}
 (AUTH/'metadata.json').write_text(json.dumps(metadata,indent=2))
 print('Prepared approved-preview package:',len(files),'files; publish root is .',flush=True)
def authorize():
 metadata=json.loads((AUTH/'metadata.json').read_text());private=serialization.load_pem_private_key(KEY.read_bytes(),password=None);KEY.unlink()
 path=f'operations/promotion-envelope-{RUN}-{ATTEMPT}.json'
 print('Waiting for run-bound encrypted authorization.',flush=True)
 for _ in range(150):
  u=f'https://api.github.com/repos/{REPO}/contents/{path}?ref='+urllib.parse.quote(BRANCH,safe='')
  req=urllib.request.Request(u,headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github.raw+json','User-Agent':'PK promotion'})
  try:
   with urllib.request.urlopen(req,timeout=20) as r:env=json.loads(r.read())
   assert env['keyId']==metadata['keyId']
   key=private.decrypt(base64.b64decode(env['key']),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
   secret=json.loads(AESGCM(key).decrypt(base64.b64decode(env['nonce']),base64.b64decode(env['ciphertext']),metadata['keyId'].encode()))
   for k in ['runId','runAttempt','siteId','bundleSHA256']:assert secret[k]==metadata[k],k
   assert re.fullmatch(r'https://netlify-mcp\.netlify\.app/proxy/[A-Za-z0-9._-]+',secret['proxy'])
   assert sha(json.dumps(records(),sort_keys=True,separators=(',',':')).encode())==metadata['bundleSHA256']
   return secret
  except urllib.error.HTTPError as e:
   if e.code!=404:raise RuntimeError('Authorization lookup failed: '+str(e.code)) from None
  time.sleep(5)
 raise RuntimeError('Authorization window expired. No upload attempted.')
def run_deploy(folder,proxy):
 print('::add-mask::'+proxy,flush=True);print('::add-mask::'+proxy.rsplit('/',1)[-1],flush=True)
 env={k:v for k,v in os.environ.items() if k not in ['GITHUB_TOKEN']}
 p=subprocess.run(['npx','-y','@netlify/mcp@latest','--site-id',SITE_ID,'--proxy-path',proxy],cwd=folder,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=600)
 output=p.stdout.replace(proxy,'[REDACTED]').replace(proxy.rsplit('/',1)[-1],'[REDACTED]')
 (EVIDENCE/'deployment.log').write_text(output)
 print(output[-7000:],flush=True)
 assert p.returncode==0,'Netlify upload/build failed; see sanitized deployment log'
def verify_live():
 files=records()
 def verify_one(item):
  path,digest=item
  if path in ['_redirects','_headers','netlify.toml']:return
  for n in range(8):
   if sha(get(web(PRODUCTION,path),attempts=2))==digest:return
   time.sleep(4)
  raise AssertionError('Published file differs: '+path)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(verify_one,files.items()))
 subprocess.run([sys.executable,str(PK/'tests/browser_v2.py'),'--base',PRODUCTION,'--public'],check=True,cwd=ROOT)
 return len(files)-sum(p in files for p in ['_redirects','_headers','netlify.toml'])
def publish():
 report={'published':False,'target':SITE_ID,'preview':PREVIEW,'previousProduction':'6ab1939ae68f1a942996df56'}
 proxy=None;attempted=False
 try:
  secret=authorize();proxy=secret.pop('proxy');secret.clear()
  assert sha(get(PRODUCTION))==(EVIDENCE/'baseline-root.sha256').read_text(),'Production changed; stop.'
  attempted=True;run_deploy(SITE,proxy);report['matchedPublishedFiles']=verify_live();report['published']=True
  print('SUCCESS: approved preview is published on the original PK Stratagems site.',flush=True)
 except Exception as e:
  report['error']=str(e)
  # Restore the previous site through its immutable deploy if publication changed the root but verification failed.
  if attempted and proxy:
   try:
    baseline=get(BASELINE)
    if get(PRODUCTION)!=baseline:
     restore=OUT/'restore';restore.mkdir(exist_ok=True)
     (restore/'index.html').write_bytes(baseline)
     (restore/'_redirects').write_text('/* '+BASELINE+':splat 200\n')
     (restore/'netlify.toml').write_text('[build]\n publish="."\n command="test -f index.html"\n')
     run_deploy(restore,proxy);assert get(PRODUCTION)==baseline;report['restoredPreviousVersion']=True
   except Exception as rollback:report['rollbackError']=type(rollback).__name__
  raise
 finally:
  KEY.unlink(missing_ok=True);(EVIDENCE/'publication.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':
 {'prepare':prepare,'publish':publish}[sys.argv[1]]()
