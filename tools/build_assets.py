"""Build local map assets from the exact user-supplied Event Companion version.
No rule scraping. A hash mismatch stops the build rather than changing layouts.
Run with --source /path/to/the/uploaded.pdf for a fully offline local build.
"""
import argparse
import hashlib
import io
import json
import pathlib
import urllib.request

import fitz
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
URL = 'https://assets.warhammer-community.com/eng_wh40k_event_companion-pl87i44rzn-a7ieny8i9x.pdf'
EXPECTED = '1f44d9fa0297f60be6c4367041a65d1a98710c68b221d8c8e22ecd1674e7525e'
PAGES = [18,20,22,23,30,32,34,35,39,41,43,44,45,47,48,49,50,52,53]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=pathlib.Path)
    args = parser.parse_args()
    if args.source:
        raw = args.source.read_bytes()
    else:
        request = urllib.request.Request(URL, headers={'User-Agent': 'Dropzone-Personal-Playbook/1.0'})
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read(30_000_001)
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED:
        raise RuntimeError(f'Event Companion differs from the approved input: {actual}')
    document = fitz.open(stream=raw, filetype='pdf')
    assert len(document) == 93
    target = ROOT / 'assets' / 'layouts'
    target.mkdir(parents=True, exist_ok=True)
    manifest = {'source': URL, 'sha256': actual, 'sourcePages': PAGES, 'maps': []}
    for number in PAGES:
        page = document[number - 1]
        # Fixed board crop, independently checked against the original dossier images.
        clip = fitz.Rect(127.5, 277.0, 468.0, 740.5)
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=clip, alpha=False)
        image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        image.save(target / f'board-{number}.webp', 'WEBP', quality=92, method=6)
        full = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        Image.frombytes('RGB', (full.width, full.height), full.samples).save(target / f'page-{number}.webp', 'WEBP', quality=90, method=6)
        manifest['maps'].append({'page': number, 'width': image.width, 'height': image.height, 'cropPdfPoints': list(clip)})
    (ROOT / 'assets' / 'build-info.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Verified source SHA-256; exported {len(PAGES)} board maps and {len(PAGES)} complete layout pages.')

if __name__ == '__main__':
    main()
