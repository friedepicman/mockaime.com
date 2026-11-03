"""Step 1: visit each problem's AoPS link and save the whole thread.

Runs on your Mac (the AoPS pages need a real browser). Saves one JSON per problem
to answer_check/aops_cache/<id>.json, and skips ids that are already cached, so you
can stop it with Ctrl-C and rerun any time.

    python answer_check/fetch_aops.py --csv "~/Downloads/problems_rows 2.csv" --limit 50
    python answer_check/fetch_aops.py --csv ... --ids 9888-10100
    python answer_check/fetch_aops.py --csv ...            # everything (~3s/problem)

Set CHROMEDRIVER=/path/to/chromedriver if Selenium can't find one by itself.
"""
import argparse
import json
import os
import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common import CACHE_DIR, load_problems, parse_ids, select_rows

MAX_POSTS = 25
MAX_POST_CHARS = 6000


def latex_text(el):
    """Text of an AoPS post with LaTeX images turned back into their source."""
    parts = []

    def walk(node):
        if node.name == "img":
            alt = node.get("alt", "")
            classes = node.get("class", [])
            if alt and any(c.startswith("latex") for c in classes):
                parts.append(alt)
            elif "asy" in " ".join(classes) or "[asy]" in alt:
                parts.append("[diagram]")
        elif node.name is None:
            parts.append(str(node))
        elif node.name == "br":
            parts.append("\n")
        elif node.name == "span" and "cmty-hide-heading" in node.get("class", []):
            parts.append(f"\n[hidden: {node.get_text(strip=True)}]\n")
        else:
            for c in node.children:
                walk(c)

    walk(el)
    text = "".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1400,2000")
    driver_path = os.environ.get("CHROMEDRIVER")
    if driver_path:
        return webdriver.Chrome(service=Service(driver_path), options=opts)
    return webdriver.Chrome(options=opts)  # Selenium Manager finds a driver


def fetch_topic(driver, url):
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.cmty-post"))
    )
    time.sleep(1.0)  # let MathJax/latex images settle
    # open hidden blocks so their content is in the DOM
    driver.execute_script(
        "document.querySelectorAll('.cmty-hide-heading').forEach(e=>{try{e.click()}catch(_){}})"
    )
    time.sleep(0.5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    title_div = soup.find("div", class_="cmty-topic-subject")
    crumbs = soup.select(".cmty-breadcrumbs a, .cmty-topic-crumbs a")
    posts = []
    for post in soup.find_all("div", class_="cmty-post")[:MAX_POSTS]:
        body = post.find("div", class_="cmty-post-body")
        if not body:
            continue
        author = post.find(class_="cmty-post-username")
        posts.append({
            "author": author.get_text(strip=True) if author else "",
            "text": latex_text(body)[:MAX_POST_CHARS],
        })
    return {
        "url": url,
        "title": title_div.get_text(strip=True) if title_div else "",
        "breadcrumbs": [a.get_text(strip=True) for a in crumbs],
        "posts": posts,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Supabase export of the problems table")
    ap.add_argument("--ids", help="e.g. 6087,6090-6100")
    ap.add_argument("--min-id", type=int)
    ap.add_argument("--max-id", type=int)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between pages")
    ap.add_argument("--refetch", action="store_true", help="ignore the cache")
    args = ap.parse_args()

    rows = select_rows(load_problems(args.csv), ids=parse_ids(args.ids),
                       min_id=args.min_id, max_id=args.max_id)
    CACHE_DIR.mkdir(exist_ok=True)
    todo = [r for r in rows if r.get("link", "").startswith("http")
            and (args.refetch or not (CACHE_DIR / f"{r['id']}.json").exists())]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(rows)} selected, {len(todo)} to fetch")
    if not todo:
        return

    driver = make_driver()
    ok = fail = 0
    try:
        for i, r in enumerate(todo, 1):
            pid, url = r["id"], r["link"].strip()
            try:
                data = fetch_topic(driver, url)
                data["id"] = pid
                (CACHE_DIR / f"{pid}.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
                ok += 1
                print(f"[{i}/{len(todo)}] {pid} {r.get('source','')}: {len(data['posts'])} posts")
            except Exception as e:  # keep going; failures are retried next run
                fail += 1
                print(f"[{i}/{len(todo)}] {pid} FAILED: {type(e).__name__}: {str(e)[:120]}")
                if fail >= 10 and ok == 0:
                    print("10 failures in a row with no successes; stopping. Is AoPS reachable?")
                    break
            time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\nStopped. Rerun the same command to continue.")
    finally:
        driver.quit()
    print(f"done: {ok} fetched, {fail} failed")


if __name__ == "__main__":
    main()
