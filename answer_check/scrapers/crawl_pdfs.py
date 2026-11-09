#!/usr/bin/env python3
"""Generic PDF crawler for contests without a dedicated scraper (CMIMC by default).

Starts at an archive page, follows links on the same site up to --depth levels, and
collects every PDF link with its link text and the page it was found on. Claude then
names each file (Contest_Year_Round_problems/solutions.pdf), and the PDFs are
downloaded into ./<contest>_pdfs/ with a manifest.csv.

    python crawl_pdfs.py --contest CMIMC --start https://cmimc.com/archive --list   # just show what it finds
    python crawl_pdfs.py --contest CMIMC --start https://cmimc.com/archive
"""
import argparse
import csv
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urldefrag, urlparse

import anthropic
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "mockaime-pdf-archiver (contact: site owner)"}
SKIP_WORDS = ("login", "logout", "signin", "sign-in", "signup", "sign-up", "register", "account",
              "cart", "checkout", "donate", "mailto:", "javascript:")
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".zip", ".mp4", ".css", ".js", ".ico")


def crawl(start, depth, delay, follow=None):
    host = urlparse(start).netloc
    seen, pdfs = set(), {}
    frontier = [(start, 0)]
    while frontier:
        url, d = frontier.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
        except requests.RequestException as e:
            print(f"  ! {url}: {e}")
            continue
        if "text/html" not in r.headers.get("content-type", ""):
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        title = (soup.title.get_text(strip=True) if soup.title else "")[:120]
        print(f"  page {url}  ({title})")
        for a in soup.find_all("a", href=True):
            link = urldefrag(urljoin(url, a["href"]))[0]
            text = " ".join(a.get_text(" ", strip=True).split())[:150]
            if link.lower().split("?")[0].endswith(".pdf"):
                pdfs.setdefault(link, {"url": link, "link_text": text, "page": url, "page_title": title})
            elif (urlparse(link).netloc == host and d < depth and link not in seen
                  and not link.lower().endswith(SKIP_EXT)
                  and not any(w in link.lower() for w in SKIP_WORDS)
                  and (not follow or follow in link)):
                frontier.append((link, d + 1))
        time.sleep(delay)
    return list(pdfs.values())


NAME_SCHEMA = {
    "type": "object",
    "properties": {"files": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "year": {"type": "integer"},
            "round": {"type": "string", "description": "e.g. Algebra, Geometry, Team, Power, Individual, Tiebreaker"},
            "kind": {"type": "string", "enum": ["problems", "solutions", "answers", "other"]},
            "filename": {"type": "string", "description": "<Contest>_<Year>_<Round>_<kind>.pdf, no spaces"},
        },
        "required": ["url", "year", "round", "kind", "filename"],
        "additionalProperties": False}}},
    "required": ["files"],
    "additionalProperties": False,
}


def _name_chunk(client, contest, chunk, model):
    msg = client.messages.create(
        model=model, max_tokens=16000,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": NAME_SCHEMA}},
        messages=[{"role": "user", "content":
            f"These PDF links were found on the {contest} math contest website. For each one, "
            f"work out the year, the round and whether it is problems, solutions, answers or "
            f"something else (schedules, rules, results, sample tests for a different event), using the URL, "
            f"the link text and the page title. When the site has several tournaments or divisions, put that "
            f"in the round (e.g. HMMT 'February Algebra' vs 'November Team', PUMaC 'Algebra A'). A file for a "
            f"different event hosted on the same site (e.g. CMWMC on the CMIMC site, HMIC on HMMT) still gets "
            f"named, with that event's name as the filename prefix. Give each a filename like "
            f"{contest}_2019_February_Algebra_problems.pdf. "
            f"Keep every URL exactly as given.\n\n{json.dumps(chunk, indent=1)}"}],
    )
    text = next((b.text for b in msg.content if b.type == "text"), "{}")
    return json.loads(text).get("files", [])


def name_with_claude(contest, links, model, cache_path):
    """Name PDFs in parallel chunks; names are cached so reruns don't ask again."""
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    todo = [l for l in links if l["url"] not in cache]
    chunks = [todo[i:i + 40] for i in range(0, len(todo), 40)]
    if chunks:
        print(f"asking Claude to name {len(todo)} PDFs ({len(chunks)} requests, about a minute)...", flush=True)
        client = anthropic.Anthropic()
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = [ex.submit(_name_chunk, client, contest, c, model) for c in chunks]
            for n, fut in enumerate(as_completed(futs), 1):
                try:
                    for f in fut.result():
                        cache[f["url"]] = f
                except Exception as e:  # one failed chunk shouldn't sink the rest; rerun retries it
                    print(f"  naming request failed: {type(e).__name__}: {e}")
                print(f"  named {n}/{len(chunks)}", flush=True)
                cache_path.write_text(json.dumps(cache, indent=1))
    return [cache[l["url"]] for l in links if l["url"] in cache]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contest", default="CMIMC")
    ap.add_argument("--start", default="https://cmimc.com/archive")
    ap.add_argument("--depth", type=int, default=1)  # cmimc.com/archive links every PDF directly
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--follow", help="only follow page links containing this text, e.g. /archives/bmt-")
    ap.add_argument("--list", action="store_true", help="only list the PDF links found")
    ap.add_argument("--model", default="claude-opus-5-5")
    args = ap.parse_args()

    print(f"Crawling {args.start} (depth {args.depth})")
    links = crawl(args.start, args.depth, args.delay, args.follow)
    print(f"found {len(links)} PDF links")
    if args.list or not links:
        for l in links:
            print(f"  {l['link_text'][:50]:50}  {l['url']}")
        return

    out_dir = Path(f"{args.contest.lower()}_pdfs")
    out_dir.mkdir(exist_ok=True)
    named = [f for f in name_with_claude(args.contest, links, args.model, out_dir / "names.json")
             if f["kind"] != "other"]
    print(f"{len(named)} problem/solution/answer PDFs to download")
    rows = []
    for i, f in enumerate(named, 1):
        name = f["filename"].replace("/", "_").replace(" ", "_")
        path = out_dir / (name if name.lower().endswith(".pdf") else name + ".pdf")
        if path.exists():
            rows.append({**f, "filename": path.name})
            continue
        try:
            r = requests.get(f["url"], headers=HEADERS, timeout=60)
            if r.ok and r.content[:4] == b"%PDF":
                path.write_bytes(r.content)
                rows.append({**f, "filename": path.name})
                print(f"[{i}/{len(named)}] {path.name}")
            else:
                print(f"[{i}/{len(named)}] skip {f['url']} ({r.status_code})")
        except requests.RequestException as e:
            print(f"[{i}/{len(named)}] error {f['url']}: {e}")
        time.sleep(random.uniform(args.delay, args.delay * 2))
    with (out_dir / "manifest.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["filename", "year", "round", "kind", "url"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    print(f"done: {len(rows)} PDFs in {out_dir}/")


if __name__ == "__main__":
    main()
