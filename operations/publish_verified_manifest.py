"""Publish the tested bundle and verify its pre-upload public-file manifest.
The Netlify CLI writes .netlify/state.json locally. It is not a public asset and
must not be added to post-deploy checks or cause a false rollback.
"""
import concurrent.futures, json, subprocess, sys, time
import promote_preview as p


def verify_live():
    files = json.loads((p.EVIDENCE / 'files.json').read_text())
    assert files and 'index.html' in files and 'doubles/index.html' in files
    assert not any(path.startswith(('.netlify/', '.git/')) for path in files)
    public_files = {
        path: digest for path, digest in files.items()
        if path not in ['_redirects', '_headers', 'netlify.toml']
    }

    def check(item):
        path, expected = item
        for attempt in range(8):
            try:
                if p.sha(p.get(p.web(p.PRODUCTION, path), attempts=2)) == expected:
                    return
            except RuntimeError:
                if attempt == 7:
                    raise
            time.sleep(4)
        raise AssertionError('Published file differs: ' + path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(check, public_files.items()))
    subprocess.run(
        [sys.executable, str(p.PK / 'tests/browser_v2.py'), '--base', p.PRODUCTION, '--public'],
        check=True, cwd=p.ROOT,
    )
    (p.EVIDENCE / 'published-manifest-check.json').write_text(json.dumps({
        'matchedPublicFiles': len(public_files),
        'manifest': 'files.json from the approved pre-upload bundle',
        'ignoredLocalCLIState': '.netlify/',
        'productionBrowserChecks': 'passed',
    }, indent=2))
    return len(public_files)


p.verify_live = verify_live
if __name__ == '__main__':
    p.publish()
