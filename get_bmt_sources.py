from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json
import re

# CONFIGURATION
CHROMEDRIVER_PATH = "/Users/jasonyuan/Documents/chromedriver-mac-arm64-137/chromedriver"
BASE_URL = "https://artofproblemsolving.com"
COMP_NAME = "BMT"  # Change as needed, e.g. "HMMT", "SMT", etc.
COMP_LINK = f"{BASE_URL}/community/c2503467_bmt_problems"  # Forum main link for the competition

# Helper functions

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

def is_year_forum(url):
    return bool(re.search(r"_(\d{4})", url))

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

def get_test_name_from_subforum(driver):
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        title_div = soup.find("div", class_="cmty-category-cell-title")
        if title_div:
            return title_div.get_text(strip=True)
    except Exception:
        pass
    return ""

def is_source_block(text):
    text_lower = text.lower()
    keywords = [
        "round", "test", "team", "algebra", "combinatorics",
        "discrete", "calculus", "geometry", "guts", "analysis", "general"
    ]
    if any(kw in text_lower for kw in keywords):
        return True
    if len(text.split()) < 5:
        return True
    return False

def get_problems_with_sources(page_url, driver, year, comp_name, subforum_name=""):
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

    # Get test name from subforum if not provided and if subforum title block exists
    if not subforum_name:
        subforum_name = get_test_name_from_subforum(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    post_blocks = soup.find_all("div", attrs={"class": lambda x: x and "cmty-view-posts-item" in x})

    current_test_name = subforum_name or ""
    link_source_map = {}

    for post in post_blocks:
        text_div = post.find("div", class_="cmty-view-post-item-text")
        if not text_div:
            continue
        text = text_div.get_text(strip=True)

        if is_source_block(text) and not post.find("a"):
            current_test_name = text
            continue

        label_div = post.find("div", class_="cmty-view-post-item-label")
        if label_div:
            prob_number = label_div.get_text(strip=True)
        else:
            prob_number = "?"

        link_div = post.find("div", class_="cmty-view-post-topic-link")
        if not link_div:
            continue
        a_tag = link_div.find("a")
        if not a_tag or not a_tag.get("href"):
            continue
        topic_link = a_tag["href"]
        if not topic_link.startswith("http"):
            topic_link = BASE_URL + topic_link

        test_clean = re.sub(r"\b(round|test|team)\b", "", current_test_name, flags=re.I).strip()

        if test_clean:
            full_source = f"{comp_name} {year} {test_clean} #{prob_number}"
        else:
            full_source = f"{comp_name} {year} #{prob_number}"

        link_source_map[topic_link] = full_source

    return link_source_map

def extract_year_from_url(url):
    match = re.search(r"_(\d{4})", url)
    if match:
        return match.group(1)
    return "unknown"

def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"Fetching year/forum links for {COMP_NAME}...")
        year_links = get_year_links(COMP_LINK)
        print(f"Found {len(year_links)} year forums.")

        all_link_source_pairs = {}

        for year_url in year_links:
            if not is_year_forum(year_url):
                print(f"Skipping non-year forum: {year_url}")
                continue

            year = extract_year_from_url(year_url)
            print(f"\nScraping year {year} at {year_url}")

            link_source_map = get_problems_with_sources(year_url, driver, year, COMP_NAME)
            if not link_source_map:
                print("No problems found directly on year page, checking subforums...")
                sub_links = get_sub_forum_links(year_url, driver)
                for sub_url in sub_links:
                    print(f" Subforum: {sub_url}")
                    sub_link_source_map = get_problems_with_sources(sub_url, driver, year, COMP_NAME)
                    all_link_source_pairs.update(sub_link_source_map)
            else:
                all_link_source_pairs.update(link_source_map)

        output_file = f"{COMP_NAME}_link_source_map.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_link_source_pairs, f, indent=2, ensure_ascii=False)

        print(f"\nFinished! Link-source mapping saved to {output_file}")

    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()
