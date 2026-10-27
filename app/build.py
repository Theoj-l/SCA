"""Build the single-file app: embed data/processed/*.json into app/template.html.

    python app/build.py

Writes app/MoveWell_HDB_Moving_Demand.html (open it in any browser; it needs
internet only for Chart.js and fonts from public CDNs) and the same file as
public/index.html, which is the only thing Vercel serves.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / 'data' / 'processed'
APP_KEYS = ['resale', 'rental', 'blocks', 'cohorts', 'flatTypes', 'privateQ', 'holidays', 'regionsSvg', 'census',
            'paSvg', 'resaleOld', 'compNat', 'rentalOldQ', 'privateQOld', 'paCtx']

bundle = {k: json.load(open(PROC / f'{k}.json')) for k in APP_KEYS}
template = (ROOT / 'app' / 'template.html').read_text(encoding='utf-8')
assert template.count('__DATA__') == 1, 'template must contain exactly one __DATA__ placeholder'
out = ROOT / 'app' / 'MoveWell_HDB_Moving_Demand.html'
html = template.replace('__DATA__', json.dumps(bundle, separators=(',', ':')))
site = ROOT / 'public' / 'index.html'; site.parent.mkdir(exist_ok=True)
for f in (out, site):
    f.write_text(html, encoding='utf-8'); print(f'wrote {f.relative_to(ROOT)} ({f.stat().st_size / 1024:.0f} KB)')
