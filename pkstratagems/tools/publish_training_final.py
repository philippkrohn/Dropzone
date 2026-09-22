"""Publish only after preview browser checks; credentials remain ephemeral in memory."""
from pathlib import Path
import hashlib,io,json,os,subprocess,time,urllib.request,urllib.error,zipfile
import release
ROOT=Path(__file__).resolve().parents[1];PUB=ROOT/'netlify-site/public';QA=ROOT/'qa';QA.mkdir(exist_ok=True)
PROD='a9b698e5-0f1d-4f39-b84d-ce52c91179a7';PREVIEW='483c7eeb-a2f5-4ae3-ae29-4b098e491304'
LIVE='https://pkstratagems.netlify.app/';BASELINE='https://6ab1939ae68f1a942996df56--pkstratagems.netlify.app/'
HASH='63f0cf70824be2dd82b668b594a90a4c9f984d58a778e5a076c174887f396f58'
result={'published':False,'baseline':BASELINE,'productionSite':PROD}
def public(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'PK-Stratagems release verification'}),timeout=60) as r:return r.read()
def request(proxy,path,method='GET',data=None,ctype=None):
 headers={'User-Agent':'PK-Stratagems authorized release'}
 if ctype:headers['Content-Type']=ctype
 try:
  with urllib.request.urlopen(urllib.request.Request(proxy+path,data=data,headers=headers,method=method),timeout=180) as r:return json.loads(r.read())
 except urllib.error.HTTPError as e:
  body=e.read(1000).decode(errors='replace');category='proxy-unauthorized' if body.strip()=='Unauthorized' else 'endpoint-error'
  raise RuntimeError(f'Netlify {method} {path}: HTTP {e.code} ({category})') from None
def deploy(site,proxy,raw):
 boundary='----PKTraining'+os.urandom(12).hex();b=io.BytesIO()
 for k in ['access_token','token','userAgent','requestId','cliVersion']:b.write(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n\r\n'.encode())
 b.write(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="source.zip"\r\nContent-Type: application/zip\r\n\r\n'.encode());b.write(raw);b.write(f'\r\n--{boundary}--\r\n'.encode())
 response=request(proxy,'/api/v1/sites/'+site+'/builds','POST',b.getvalue(),'multipart/form-data; boundary='+boundary);did=response.get('deploy_id')
 assert did,'Build response has no deploy identifier'
 print('Started deploy',site,did,flush=True)
 for _ in range(100):
  d=request(proxy,'/api/v1/deploys/'+did)
  assert d['site_id']==site
  if d['state']=='ready':return d
  if d['state'] in ['error','failed']:raise RuntimeError('Netlify build failed: '+did)
  time.sleep(4)
 raise TimeoutError('Netlify build did not finish')
def verify(base,label):
 # Every newly served file must match local bytes, including preserved Doubles assets.
 count=0
 for p in sorted(PUB.rglob('*')):
  if not p.is_file() or p.name=='_redirects':continue
  rel=p.relative_to(PUB).as_posix();data=public(base+urllib.parse.quote(rel,safe='/._-'))
  assert hashlib.sha256(data).digest()==hashlib.sha256(p.read_bytes()).digest(),label+': bytes differ '+rel
  count+=1
 subprocess.run(['python',str(ROOT/'tests/browser_v2.py'),'--base',base,'--public','--case-label',label],check=True)
 return {'filesMatch':count,'browser':'passed'}
try:
 print('Waiting for encrypted authorization',flush=True);secret=release.wait_envelope()
 for k in ['previewProxy','productionProxy']:secret[k]=release.proxy_from(secret[k])
 files=release.bundle_files(ROOT/'netlify-site')
 assert release.bundle_sha(files)==json.loads((ROOT/'release-public/metadata.json').read_text())['bundleSHA256']
 assert hashlib.sha256(public(LIVE)).hexdigest()==HASH,'Production changed; stop rather than overwrite.'
 rawio=io.BytesIO()
 with zipfile.ZipFile(rawio,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted((ROOT/'netlify-site').rglob('*')):
   if p.is_file():z.write(p,p.relative_to(ROOT/'netlify-site').as_posix())
 raw=rawio.getvalue()
 stage=deploy(PREVIEW,secret['previewProxy'],raw);result['previewDeploy']=stage['id'];stageurl=stage['deploy_ssl_url'].rstrip('/')+'/'
 result['previewURL']=stageurl;result['preview']=verify(stageurl,'preview')
 assert hashlib.sha256(public(LIVE)).hexdigest()==HASH,'Concurrent production update; stop.'
 prod=deploy(PROD,secret['productionProxy'],raw);result['productionDeploy']=prod['id'];result['production']=verify(LIVE,'production');result['published']=True
 print(json.dumps(result,ensure_ascii=False),flush=True)
except Exception as e:
 result['error']=type(e).__name__+': '+str(e)
 # Never assert success after a failed production verification. Baseline ID is recorded for restoration.
 print('Release stopped:',result['error'],flush=True)
 raise
finally:
 (QA/'release-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 Path(os.environ.get('RUNNER_TEMP','/tmp'),'pk-quiz-release-private.pem').unlink(missing_ok=True)
