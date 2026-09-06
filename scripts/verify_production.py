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
failed=[]
for url,marker in targets:
    ok=False; last=""
    for _ in range(12):
        try:
            with urlopen(Request(url,headers={"User-Agent":"astroneer-wiki-runtime-audit/1.0"}),timeout=20) as r:
                body=r.read().decode("utf-8","replace")
                if r.status==200 and marker in body: ok=True; break
                last=f"HTTP {r.status}; marker missing"
        except (URLError,HTTPError,TimeoutError) as e: last=repr(e)
        time.sleep(5)
    print(("OK " if ok else "FAIL ")+url)
    if not ok: failed.append((url,last))
if failed:
    for x in failed: print("ERROR:",x)
    raise SystemExit(1)
print(json.dumps({"production_checked":len(targets),"production_failed":0},ensure_ascii=False))
