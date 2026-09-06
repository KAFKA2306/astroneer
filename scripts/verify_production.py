#!/usr/bin/env python3
import json,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError

ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/"data/wiki.json").read_text(encoding="utf-8"))
base=m["production_url"].rstrip("/")+"/"
targets=[(base,"ASTRONEER 日本語Wiki")]
targets += [(base+f'category/{c["slug"]}/',c["title"]) for c in m["categories"]]
targets += [(base+f'wiki/{a["slug"]}/',a["title"]) for a in m["articles"] if a["status"]=="implemented"]
asset_targets=[
    (base+"assets/wiki.css",[
        'kafka-design:managed-start',
        '@import "./kafka-design/kafka-tokens.css";',
        'var(--k-color-surface)',
    ]),
    (base+"assets/kafka-design/kafka-tokens.css",[
        "color-scheme: light;",
        '[data-theme="dark"]',
        "@media (prefers-color-scheme: dark)",
    ]),
]
failed=[]

def fetch(url):
    with urlopen(Request(url,headers={"User-Agent":"astroneer-wiki-runtime-audit/1.0"}),timeout=20) as r:
        return r.status,r.read().decode("utf-8","replace")

for url,marker in targets:
    ok=False; last=""
    for _ in range(12):
        try:
            status,body=fetch(url)
            if status==200 and marker in body: ok=True; break
            last=f"HTTP {status}; marker missing"
        except (URLError,HTTPError,TimeoutError) as e: last=repr(e)
        time.sleep(5)
    print(("OK " if ok else "FAIL ")+url)
    if not ok: failed.append((url,last))

for url,markers in asset_targets:
    ok=False; last=""
    for _ in range(12):
        try:
            status,body=fetch(url)
            missing=[marker for marker in markers if marker not in body]
            if status==200 and not missing: ok=True; break
            last=f"HTTP {status}; missing={missing}"
        except (URLError,HTTPError,TimeoutError) as e: last=repr(e)
        time.sleep(5)
    print(("OK " if ok else "FAIL ")+url)
    if not ok: failed.append((url,last))

if failed:
    for x in failed: print("ERROR:",x)
    raise SystemExit(1)
print(json.dumps({"production_checked":len(targets)+len(asset_targets),"production_failed":0},ensure_ascii=False))
