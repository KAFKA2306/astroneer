#!/usr/bin/env python3
import argparse, json, re, sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "wiki.json"
IO = ROOT / "io"
README = ROOT / "README.md"

def load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))

def internal_links(path):
    text = path.read_text(encoding="utf-8")
    return re.findall(r'href=["\\\']([^"\\\']+)["\\\']', text)

def resolve_link(source, href):
    if href.startswith(("http://","https://","mailto:","javascript:","#")):
        return None
    href = unquote(href.split("#",1)[0].split("?",1)[0])
    if not href:
        return None
    target = (source.parent / href).resolve()
    if href.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args=ap.parse_args()
    m=load()
    cats={c["slug"] for c in m["categories"]}
    arts=m["articles"]
    slugs=[a["slug"] for a in arts]
    errors=[]
    if len(slugs)!=len(set(slugs)): errors.append("duplicate slugs")
    for a in arts:
        if a["category"] not in cats: errors.append(f'unknown category: {a["slug"]}')
        if not a.get("source"): errors.append(f'missing source: {a["slug"]}')
        if a["status"] not in {"planned","implemented"}: errors.append(f'bad status: {a["slug"]}')
        if a["status"]=="implemented":
            p=IO/"wiki"/a["slug"]/"index.html"
            if not p.exists():
                errors.append(f'implemented file missing: {a["slug"]}')
            else:
                page_text=p.read_text(encoding="utf-8")
                if a["source"] not in page_text: errors.append(f'implemented source not rendered: {a["slug"]}')
                if a.get("last_verified") and a["last_verified"] not in page_text: errors.append(f'implemented last_verified not rendered: {a["slug"]}')
            if not a.get("last_verified"): errors.append(f'implemented last_verified missing: {a["slug"]}')
    expected={a["slug"] for a in arts if a["status"]=="implemented"}
    actual={p.parent.name for p in (IO/"wiki").glob("*/index.html")} if (IO/"wiki").exists() else set()
    extras=actual-expected
    if extras: errors.append("unmanifested article pages: "+",".join(sorted(extras)))
    prod=m["production_url"]
    if not README.exists() or README.read_text(encoding="utf-8").splitlines()[0].strip()!=prod:
        errors.append("README first line is not production_url")
    broken=[]
    htmls=list(IO.rglob("*.html"))
    for p in htmls:
        page_text=p.read_text(encoding="utf-8")
        rel=p.relative_to(ROOT)
        if not re.search(r'<html\\b[^>]*\\bdata-theme=["\\\']light["\\\']', page_text):
            errors.append(f"light theme policy missing: {rel}")
        if re.search(r'<style\\b|\\sstyle=["\\\']', page_text, re.I):
            errors.append(f"inline style bypasses canonical design: {rel}")
        if "assets/wiki.css" not in page_text:
            errors.append(f"canonical wiki.css missing: {rel}")
    for p in htmls:
        for href in internal_links(p):
            t=resolve_link(p,href)
            if t is not None and ROOT in t.parents and not t.exists():
                broken.append(f"{p.relative_to(ROOT)} -> {href}")
    if broken: errors += ["broken internal link: "+x for x in broken]
    # Rendered navigation must be a derivative of the manifest, not a second authority.
    top = IO / "index.html"
    top_text = top.read_text(encoding="utf-8") if top.exists() else ""
    top_slugs = re.findall(r'data-slug=["\\\']([^"\\\']+)["\\\']', top_text)
    manifest_slugs = set(slugs)
    if set(top_slugs) != manifest_slugs:
        errors.append("top article list is out of sync with manifest")
    orphan = 0
    for c in m["categories"]:
        page = IO / "category" / c["slug"] / "index.html"
        if not page.exists():
            errors.append(f'category page missing: {c["slug"]}')
            continue
        rendered = set(re.findall(r'data-slug=["\\\']([^"\\\']+)["\\\']', page.read_text(encoding="utf-8")))
        expected_cat = {a["slug"] for a in arts if a["category"] == c["slug"]}
        if rendered != expected_cat:
            errors.append(f'category page out of sync: {c["slug"]}')
    for a in arts:
        if a["status"] == "implemented":
            href = f'wiki/{a["slug"]}/'
            cat_href = f'../../wiki/{a["slug"]}/'
            cat_page = IO / "category" / a["category"] / "index.html"
            if href not in top_text or cat_href not in cat_page.read_text(encoding="utf-8"):
                orphan += 1
    if orphan:
        errors.append(f"orphan implemented articles: {orphan}")

    # World/progression canonical data checks.
    planets_data=json.loads((ROOT/"data"/"planets.json").read_text(encoding="utf-8"))
    planet_slugs={p["slug"] for p in planets_data["planets"]}
    required_planets={"sylva","desolo","calidor","vesania","novus","glacio","atrox","aeoluz"}
    if planet_slugs != required_planets: errors.append("planet canonical set mismatch")
    for p in planets_data["planets"]:
        for key in ("resources","gases","gateway_chambers","gateway_power","core_resource","hazards","source"):
            if key not in p: errors.append(f'planet missing {key}: {p["slug"]}')
        if not (IO/"wiki"/p["slug"]/"index.html").exists(): errors.append(f'planet page missing: {p["slug"]}')

    gal_data=json.loads((ROOT/"data"/"galastropods.json").read_text(encoding="utf-8"))
    gal_slugs={g["slug"] for g in gal_data["galastropods"]}
    required_gals={"sylvie","usagi","stilgar","princess","rogal","bestefar","enoki"}
    if gal_slugs != required_gals: errors.append("galastropod canonical set mismatch")
    for g in gal_data["galastropods"]:
        for key in ("planet","terrarium","ability","favorites","source"):
            if key not in g: errors.append(f'galastropod missing {key}: {g["slug"]}')
        if not (IO/"wiki"/g["slug"]/"index.html").exists(): errors.append(f'galastropod page missing: {g["slug"]}')

    mission_data=json.loads((ROOT/"data"/"missions.json").read_text(encoding="utf-8"))
    mission_slugs=[]
    for mission in mission_data["missions"]:
        mission_slugs.append(mission["slug"])
        for key in ("name","objectives","description","rewards","prerequisites"):
            if key not in mission: errors.append(f'mission missing {key}: {mission["slug"]}')
    if len(mission_slugs) != len(set(mission_slugs)): errors.append("duplicate mission slugs")
    mission_html=(IO/"wiki"/"missions"/"index.html").read_text(encoding="utf-8")
    rendered=set(re.findall(r'data-mission=["\\\']([^"\\\']+)["\\\']', mission_html))
    if rendered != set(mission_slugs): errors.append("missions page is out of sync with data/missions.json")

    implemented=sum(a["status"]=="implemented" for a in arts)
    total=len(arts)
    missing=total-implemented
    missing_sources=sum(not a.get("source") for a in arts)
    unverified=sum(a["status"]=="planned" or not a.get("last_verified") for a in arts)
    print(json.dumps({
      "total":total,"implemented":implemented,"missing":missing,
      "orphan":orphan,"broken_internal_links":len(broken),
      "missing_sources":missing_sources,"unverified_required_fields":unverified
    }, ensure_ascii=False))
    if errors:
        for e in errors: print("ERROR:",e,file=sys.stderr)
        return 1
    if args.strict and (missing or missing_sources or unverified):
        print("ERROR: strict coverage audit failed",file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    raise SystemExit(main())
