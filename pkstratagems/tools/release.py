"""Scoped Netlify upload from an ephemeral runner. No plaintext credentials on disk."""
import base64,hashlib,io,json,os,re,subprocess,time,urllib.request,urllib.error,uuid,zipfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT=Path(__file__).resolve().parents[1]
PROD='a9b698e5-0f1d-4f39-b84d-ce52c91179a7';PREVIEW='483c7eeb-a2f5-4ae3-ae29-4b098e491304'
URLS={PROD:'https://pkstratagems.netlify.app/',PREVIEW:'https://pkstratagems-vorschau.netlify.app/'}
EXPECTED='2d9bc0e99c499dd5ef5fcdae1c154e08db1738aa749c26e50c77ff8a23cf024b'
RUN=os.environ['GITHUB_RUN_ID'];ATTEMPT=os.environ['GITHUB_RUN_ATTEMPT']
branch='feature/faction-quizzes';repository='philippkrohn/Dropzone'
keypath=Path(os.environ['RUNNER_TEMP'])/('pk-quiz-'+RUN+'-'+ATTEMPT+'.pem')
private=serialization.load_pem_private_key(keypath.read_bytes(),password=None)
keypath.unlink()
pub=private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
keyid=hashlib.sha256(pub).hexdigest()
bundle=Path(os.environ['RUNNER_TEMP'])/'pk-quiz-release.zip';bundlebytes=bundle.read_bytes();bundlehash=hashlib.sha256(bundlebytes).hexdigest()
def public_get(url):
 with urllib.request.urlopen(url,timeout=45) as r:return r.read()
def netlify_request(proxy,path,method='GET',data=None,headers=None):
 # Only the two endpoints explicitly issued by the Netlify tool are used.
 assert re.fullmatch(r'/api/v1/deploys/[a-zA-Z0-9_-]+',path) or (method=='POST' and path in [f'/api/v1/sites/{s}/builds' for s in [PROD,PREVIEW]])
 request=urllib.request.Request(proxy.rstrip('/')+path,data=data,method=method,headers=headers or {})
 try:
  with urllib.request.urlopen(request,timeout=90) as r:return json.loads(r.read())
 except urllib.error.HTTPError as e:raise RuntimeError('Netlify endpoint returned HTTP '+str(e.code)) from None
 except Exception:raise RuntimeError('Netlify request failed; credential-bearing URL omitted') from None
print('Waiting for encrypted, run-bound release authorization.',flush=True)
secret=None
for _ in range(120):
 path=f'operations/quiz-envelope-{RUN}-{ATTEMPT}.json'
 u=f'https://api.github.com/repos/{repository}/contents/{path}?ref=feature%2Ffaction-quizzes'
 request=urllib.request.Request(u,headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github.raw+json','User-Agent':'PK-Quiz-Release'})
 try:
  with urllib.request.urlopen(request,timeout=20) as r:env=json.loads(r.read())
  if env.get('keyId')!=keyid:raise RuntimeError('Envelope key does not match this runner.')
  aes=private.decrypt(base64.b64decode(env['key']),padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
  secret=json.loads(AESGCM(aes).decrypt(base64.b64decode(env['nonce']),base64.b64decode(env['ciphertext']),keyid.encode()))
  break
 except urllib.error.HTTPError as e:
  if e.code!=404:raise RuntimeError('Could not read release envelope: '+str(e.code)) from None
 time.sleep(10)
if secret is None:raise RuntimeError('Authorization window expired. Nothing was deployed.')
assert secret['runId']==RUN and secret['runAttempt']==ATTEMPT and secret['bundleSHA256']==bundlehash
for name in ['previewProxy','productionProxy']:
 value=secret[name]
 assert re.fullmatch(r'https://netlify-mcp\.netlify\.app/proxy/[A-Za-z0-9._-]+',value)
 print('::add-mask::'+value,flush=True)
 print('::add-mask::'+value.rsplit('/',1)[-1],flush=True)
print('Release authorization decrypted in memory; starting preview.',flush=True)
def deploy(site,proxy,payload=bundlebytes):
 boundary='----NetlifyFormBoundary'+uuid.uuid4().hex
 data=(f'--{boundary}\r\nContent-Disposition: form-data; name="zip"; filename="pk-quiz.zip"\r\nContent-Type: application/zip\r\n\r\n'.encode()+payload+f'\r\n--{boundary}--\r\n'.encode())
 response=netlify_request(proxy,f'/api/v1/sites/{site}/builds','POST',data,{'Content-Type':'multipart/form-data; boundary='+boundary,'Content-Length':str(len(data)),'User-Agent':'netlify-mcp'})
 if isinstance(response,list):response=response[0]
 did=response.get('deploy_id');assert isinstance(did,str) and re.fullmatch(r'[a-zA-Z0-9_-]+',did),'No deploy id returned.'
 print('Netlify deployment started: '+site+' / '+did,flush=True)
 for _ in range(100):
  d=netlify_request(proxy,'/api/v1/deploys/'+did)
  if d.get('state')=='ready':
   print('Netlify deployment ready: '+did,flush=True);return did
  if d.get('state') in ['error','rejected']:raise RuntimeError('Netlify build did not succeed: '+did)
  time.sleep(6)
 raise RuntimeError('Netlify build timeout: '+did)
def verify(base):
 for _ in range(30):
  try:
   root=public_get(base).decode()
   if 'class="quiz-link"' in root:break
  except Exception:pass
  time.sleep(3)
 assert 'class="quiz-link"' in root,'New root not visible.'
 original=public_get('https://6aaaf71c159714ef2f9ac9f5--pkstratagems.netlify.app/').decode()
 assert re.findall(r'<script\b[^>]*>(.*?)</script>',root,re.S)==re.findall(r'<script\b[^>]*>(.*?)</script>',original,re.S),'Legacy script changed.'
 # The old Doubles content and embedded public files must remain available.
 old=public_get('https://6aaaf71c159714ef2f9ac9f5--pkstratagems.netlify.app/doubles/')
 legacy=public_get(base+'doubles/')
 assert len(legacy)>500 and re.findall(rb'<script\b[^>]*>(.*?)</script>',old,re.S)==re.findall(rb'<script\b[^>]*>(.*?)</script>',legacy,re.S),'Doubles fallback differs.'
 subprocess.run(['python','tests/browser.py','--base',base],cwd=ROOT,check=True)
 return {'rootScriptUnchanged':True,'doublesAvailable':True,'quizBrowserTests':True}
result={'bundleSHA256':bundlehash,'previousProductionDeploy':'6aaaf71c159714ef2f9ac9f5','productionChanged':False}
# Avoid overwriting a concurrent production change.
assert hashlib.sha256(public_get(URLS[PROD])).hexdigest()==EXPECTED,'Production changed; stop.'
result['previewDeploy']=deploy(PREVIEW,secret['previewProxy'])
result['previewChecks']=verify(URLS[PREVIEW])
assert hashlib.sha256(public_get(URLS[PROD])).hexdigest()==EXPECTED,'Production changed during preview; stop.'
result['productionDeploy']=deploy(PROD,secret['productionProxy']);result['productionChanged']=True
try:result['productionChecks']=verify(URLS[PROD]);result['passed']=True
except Exception:
 # Restore the former root and forward every remaining route to the immutable old deploy.
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('netlify.toml','[build]\n publish="public"\n command="echo Restore previous PK Stratagems"\n')
  z.writestr('public/index.html',public_get('https://6aaaf71c159714ef2f9ac9f5--pkstratagems.netlify.app/'))
  z.writestr('public/_redirects','/* https://6aaaf71c159714ef2f9ac9f5--pkstratagems.netlify.app/:splat 200\n')
 result['restoredDeploy']=deploy(PROD,secret['productionProxy'],buf.getvalue());result['passed']=False
 (ROOT/'qa/release-report.json').write_text(json.dumps(result,indent=2))
 raise RuntimeError('Production checks failed. Former website restored.') from None
(ROOT/'qa/release-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
# Secrets are intentionally never persisted or included in artifacts.
secret.clear()
