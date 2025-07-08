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
COMP_NAME = "HMMT"  # Customize this (e.g., "HMMT", "PUMaC")
COMP_LINK = f"{BASE_URL}/community/c2881068_hmnt__hmmt_november"  # Replace with desired forum link


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

def get_problems_with_sources(page_url, driver, year, comp_name, subforum_name=""):
    print(f"Loading page: {page_url}")
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

    if not subforum_name:
        title_div = soup.find("div", class_="cmty-category-cell-title")
        if title_div:
            subforum_name = title_div.get_text(strip=True)
            print(f"Subforum name found from page: '{subforum_name}'")

    post_blocks = soup.find_all("div", class_="cmty-view-posts-item")

    current_test_name = subforum_name or ""
    link_source_map = {}

    for i, post in enumerate(post_blocks, start=1):
        text_div = post.find("div", class_="cmty-view-post-item-text")
        if not text_div:
            print(f"[{i}] Skipping block with no text div")
            continue
        text = text_div.get_text(strip=True)

        has_link = bool(post.find("a"))

        if not has_link:
            current_test_name = text
            print(f"[{i}] Source block found: '{text}' -> current_test_name updated")
            continue

        label_div = post.find("div", class_="cmty-view-post-item-label")
        prob_number = label_div.get_text(strip=True) if label_div else "?"
        if not label_div:
            print(f"[{i}] Warning: problem block with missing label; using '?'")

        link_div = post.find("div", class_="cmty-view-post-topic-link")
        if not link_div:
            print(f"[{i}] Warning: missing topic link div; skipping")
            continue
        a_tag = link_div.find("a")
        if not a_tag or not a_tag.get("href"):
            print(f"[{i}] Warning: missing href in <a>; skipping")
            continue
        topic_link = a_tag["href"]
        if not topic_link.startswith("http"):
            topic_link = BASE_URL + topic_link

        test_clean = current_test_name
        test_clean = re.sub(rf"\b{year}\b", "", test_clean)
        test_clean = re.sub(rf"\b{comp_name}\b", "", test_clean, flags=re.I)
        test_clean = re.sub(r"\b(round|test)\b", "", test_clean, flags=re.I)
        test_clean = re.sub(r"\s+", " ", test_clean).strip()

        if test_clean:
            full_source = f"{comp_name} {year} {test_clean} #{prob_number}"
        else:
            full_source = f"{comp_name} {year} #{prob_number}"

        print(f"[{i}] Problem found: {full_source} -> {topic_link}")
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

            # Always extract from both year page and subforums
            link_source_map = get_problems_with_sources(year_url, driver, year, COMP_NAME)
            all_link_source_pairs.update(link_source_map)

            sub_links = get_sub_forum_links(year_url, driver)
            for sub_url in sub_links:
                print(f" Subforum: {sub_url}")
                sub_link_source_map = get_problems_with_sources(sub_url, driver, year, COMP_NAME)
                all_link_source_pairs.update(sub_link_source_map)

        output_file = f"{COMP_NAME}_link_source_map.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_link_source_pairs, f, indent=2, ensure_ascii=False)

        print(f"\nFinished! Link-source mapping saved to {output_file}")

    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()
