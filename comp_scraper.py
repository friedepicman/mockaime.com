from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json
import re

# ✅ CONFIGURATION
CHROMEDRIVER_PATH = "/Users/jasonyuan/Documents/chromedriver-mac-arm64-137/chromedriver"
BASE_URL = "https://artofproblemsolving.com"
COMP_NAME = "BMT"  # Customize this (e.g., "HMMT", "PUMaC")
COMP_LINK = f"{BASE_URL}/community/c2503467_bmt_problems"  # Replace with desired forum link

def get_year_links(main_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(main_url)

    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    links = []
    for div in soup.find_all("div", attrs={"class": lambda c: c and "cmty-category-cell-heading" in c}):
        a_tag = div.find("a", class_="cmty-full-cell-link")
        if a_tag and a_tag.get("href"):
            href = a_tag["href"]
            if href.strip():
                links.append(BASE_URL + href)

    return sorted(set(links), reverse=True)

def get_sub_forum_links(page_url, driver):
    driver.get(page_url)

    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    sub_links = []
    for div in soup.find_all("div", class_="cmty-category-cell-heading"):
        a_tag = div.find("a", class_="cmty-full-cell-link")
        if a_tag and a_tag.get("href"):
            sub_links.append(BASE_URL + a_tag["href"])

    return sub_links

def get_problems_from_page(page_url, driver):
    driver.get(page_url)

    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, "html.parser")
    problems = []

    post_blocks = soup.find_all("div", attrs={"class": lambda x: x and "cmty-view-posts-item" in x})
    print(f"🔎 Found {len(post_blocks)} post blocks on page {page_url}")

    for post in post_blocks:
        text_div = post.find("div", class_="cmty-view-post-item-text")
        link_div = post.find("div", class_="cmty-view-post-topic-link")

        if not text_div or not link_div:
            continue

        a_tag = link_div.find("a")
        if not a_tag or not a_tag.get("href"):
            continue
        topic_link = BASE_URL + a_tag["href"]

        fragments = []
        for element in text_div.descendants:
            if element.name == "img" and "latex" in element.get("class", []):
                fragments.append(element.get("alt", "").strip())
            elif element.name is None:
                text = element.strip()
                if text != ".":
                    fragments.append(text)
            elif element.name:
                fragments.append(element.get_text(strip=True))

        problem_text = " ".join(fragments).replace("\n", " ").strip()
        word_count = len(problem_text.split())
        if word_count < 2 or (word_count < 3 and "round" in problem_text.lower()):
            continue

        if problem_text:
            problems.append({
                "text": problem_text,
                "topic_link": topic_link
            })

    return problems

def get_latex_aware_text(element):
    fragments = []

    def walk(node):
        if node.name == "img" and any(cls in node.get("class", []) for cls in ["latex", "latexcenter"]):
            alt = node.get("alt", "").strip()
            fragments.append(alt)
        elif node.name is None:
            text = node.strip()
            if text and text != ".":
                fragments.append(text)
        elif node.name in ["br"]:
            fragments.append("\n")
        else:
            for child in node.children:
                walk(child)

    walk(element)
    return " ".join(fragments).replace("  ", " ").replace("\n ", "\n").strip()

def get_solution_from_topic(topic_url, driver):
    driver.get(topic_url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    title_div = soup.find("div", class_="cmty-topic-subject")
    title = title_div.get_text(strip=True) if title_div else None

    posts = soup.find_all("div", class_="cmty-post-body")
    if len(posts) < 2:
        return title, None
    post = posts[1]

    solution_header = post.find("span", class_="cmty-hide-heading", string=lambda t: t and "solution" in t.lower())
    if solution_header:
        solution_div = solution_header.find_next("div", class_="cmty-hide-content")
    else:
        solution_div = post.find("div", class_="cmty-post-html")

    if not solution_div:
        return title, None

    return title, get_latex_aware_text(solution_div)

if __name__ == "__main__":
    print("🔍 Launching browser...")
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    all_year_data = []

    try:
        print(f"📂 Fetching {COMP_NAME} year links...")
        year_links = get_year_links(COMP_LINK)
        print(f"✅ Found {len(year_links)} contest years")

        for year_url in year_links:
            print(f"\n📄 Scraping problems from: {year_url}")
            problems = get_problems_from_page(year_url, driver)

            if not problems:
                print("🔁 No problems found directly — checking sub-forums...")
                sub_links = list(set(get_sub_forum_links(year_url, driver)))
                for sub_url in sub_links:
                    print(f"↳ Sub-forum: {sub_url}")
                    problems.extend(get_problems_from_page(sub_url, driver))

            print(f"🧮 Total problems found: {len(problems)}")

            year_id_match = re.search(r"/(\d{4})_", year_url)
            year_id = year_id_match.group(1) if year_id_match else "unknown"

            enriched_problems = []
            for i, prob in enumerate(problems, 1):
                print(f"🔗 Scraping solution for problem {i}/{len(problems)}...")
                title, solution = get_solution_from_topic(prob["topic_link"], driver)
                enriched_problems.append({
                    "title": title,
                    "text": prob["text"],
                    "solution": solution,
                    "link": prob["topic_link"]
                })

            all_year_data.append({
                "year": year_id,
                "problems": enriched_problems
            })

        output_file = f"{COMP_NAME}_problems_with_solutions.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_year_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ All problems + solutions saved to {output_file}")

    finally:
        driver.quit()
        print("🚪 Browser closed.")
