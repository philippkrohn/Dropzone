from pathlib import Path
import os,json,zipfile,hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
ROOT=Path(__file__).resolve().parents[1]
RUN=os.environ['GITHUB_RUN_ID'];ATTEMPT=os.environ['GITHUB_RUN_ATTEMPT']
key=rsa.generate_private_key(public_exponent=65537,key_size=4096)
private=Path(os.environ['RUNNER_TEMP'])/('pk-quiz-'+RUN+'-'+ATTEMPT+'.pem')
fd=os.open(private,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
pub=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
out=ROOT/'release-public';out.mkdir(exist_ok=True);(out/'public.pem').write_bytes(pub)
bundle=Path(os.environ['RUNNER_TEMP'])/'pk-quiz-release.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,9) as z:
 for p in sorted((ROOT/'netlify-site').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(ROOT/'netlify-site'))
metadata={'runId':RUN,'runAttempt':ATTEMPT,'keyId':hashlib.sha256(pub).hexdigest(),'bundleSHA256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'files':len(zipfile.ZipFile(bundle).namelist())}
(out/'metadata.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata,indent=2))
