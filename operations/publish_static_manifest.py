"""Publish the verified bundle and compare only the pre-deployment public manifest.
The Netlify CLI creates .netlify/state.json locally; that is not a public asset
and must never be requested from the production website or cause a rollback.
"""
import concurrent.futures
import json
import subprocess
import sys
import time
import promote_preview as promotion


def verify_live():
    files = json.loads((promotion.EVIDENCE / 'files.json').read_text())
    assert all(not p.startswith('.') and '/.netlify/' not in p for p in files)
    metadata = json.loads((promotion.AUTH / 'metadata.json').read_text())
    manifest_hash = promotion.sha(json.dumps(files, sort_keys=True, separators=(',', ':')).encode())
    assert manifest_hash == metadata['bundleSHA256'], 'The approved manifest changed.'
    configuration_files = {'_redirects', '_headers', 'netlify.toml'}
    public_files = {p: digest for p, digest in files.items() if p not in configuration_files}
    assert 'index.html' in public_files and 'doubles/index.html' in public_files
    assert 'quiz/index.html' in public_files and 'fraktionen/index.html' in public_files

    def verify_one(item):
        path, digest = item
        for attempt in range(8):
            if promotion.sha(promotion.get(promotion.web(promotion.PRODUCTION, path), attempts=2)) == digest:
                return
            time.sleep(4)
        raise AssertionError('Published file differs: ' + path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(verify_one, public_files.items()))
    subprocess.run([
        sys.executable, str(promotion.PK / 'tests/browser_v2.py'),
        '--base', promotion.PRODUCTION, '--public'
    ], check=True, cwd=promotion.ROOT)
    (promotion.EVIDENCE / 'public-file-verification.json').write_text(json.dumps({
        'passed': True, 'publicFilesMatched': len(public_files),
        'manifestSHA256': manifest_hash,
        'excludedConfigurationFiles': sorted(set(files) & configuration_files),
        'cliMetadataNotPublic': True
    }, indent=2))
    return len(public_files)


promotion.verify_live = verify_live
if __name__ == '__main__':
    promotion.publish()
