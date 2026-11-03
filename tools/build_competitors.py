"""Summarise ACRA's moving companies into data/processed/competitors.json (used by the app and the notebook).

    python tools/build_competitors.py

Input: data/processed/acra_movers.csv, written by tools/fetch_acra_movers.py (ACRA "Information on
Corporate Entities", every entity whose primary or secondary SSIC code is 49232 "Moving services").
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / 'data' / 'processed' / 'acra_movers.csv', ROOT / 'data' / 'processed' / 'competitors.json'
AS_OF = 2026

# Registered address -> region, by the first two digits of the postal code (postal sector). Approximate:
# sectors follow postal districts, not planning-area boundaries, and a firm's registered address is not
# always where its lorries are parked.
SECTOR_REGION = {**{f'{i:02d}': 'Central' for i in list(range(1, 46)) + [57, 58, 59, 77, 78]},
                 **{f'{i:02d}': 'East' for i in list(range(46, 53)) + [81]},
                 **{f'{i:02d}': 'North-East' for i in [53, 54, 55, 56, 79, 80, 82]},
                 **{f'{i:02d}': 'West' for i in range(60, 72)},
                 **{f'{i:02d}': 'North' for i in [72, 73, 75, 76]}}
MOVING_WORDS = 'MOVER|MOVING|REMOVAL|RELOCAT'


def summarise(df):
    df = df.fillna('na')
    live = df.entity_status_description.str.startswith('Live')
    prim = df.primary_ssic_code.str.strip() == '49232'
    year = pd.to_numeric(df.registration_incorporation_date.str[:4], errors='coerce')
    L = df[live]
    words = (L.entity_name + ' ' + L.primary_user_described_activity + ' ' + L.secondary_user_described_activity).str.upper()
    kind = L.entity_type_description.map(lambda t: 'sole' if t.startswith('Sole') else 'company' if t == 'Local Company' else 'other')
    region = L.postal_code.str.strip().str.zfill(6).str[:2].map(SECTOR_REGION).fillna('Unknown')
    regs = {}
    for y in range(1997, AS_OF + 1):
        m = prim & (year == y)
        regs[str(y)] = [int(m.sum()), int((m & live).sum())]
    return {
        'asOf': AS_OF, 'entities': int(len(df)), 'live': int(live.sum()), 'livePrimary': int((live & prim).sum()),
        'liveByKind': {k: int(v) for k, v in kind.value_counts().items()},
        'officersMedian': float(pd.to_numeric(L.no_of_officers, errors='coerce').median()),
        'liveMovingWords': int(words.str.contains(MOVING_WORDS).sum()),
        'liveAgeMedian': float((AS_OF - year[live]).median()),
        'regs': regs,
        'liveByRegion': {k: int(v) for k, v in region.value_counts().items()},
    }


if __name__ == '__main__':
    c = summarise(pd.read_csv(SRC, dtype=str))
    OUT.write_text(json.dumps(c, indent=1)); print(f'wrote {OUT.relative_to(ROOT)}: {c["live"]:,} live movers ({c["livePrimary"]:,} as main activity)')
