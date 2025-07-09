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
COMP_NAME = "PUMaC"  # Customize this (e.g., "HMMT", "PUMaC")
COMP_LINK = f"{BASE_URL}/community/c3426_princeton_university_math_competition"  # Replace with desired forum link


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
    # Updated to catch both "cmty-category-cell-heading" and "cmty-category-cell-heading cmty-cat-cell-top-legit"
    for div in soup.find_all("div", attrs={"class": lambda c: c and "cmty-category-cell-heading" in c}):
        a_tag = div.find("a", class_="cmty-full-cell-link")
        if a_tag and a_tag.get("href"):
            href = a_tag["href"]
            if href.strip():
                full_url = BASE_URL + href
                # Filter out the current page URL
                if full_url != main_url:
                    links.append(full_url)

    return sorted(set(links), reverse=True)

def get_sub_forum_links(page_url, driver):
    driver.get(page_url)
    time.sleep(3)  # Give more time for page to load

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
    sub_links = set()
    
    print(f"🔍 Analyzing page structure for: {page_url}")
    
    # Target the specific structure: div.cmty-category-cell-heading containing a.cmty-full-cell-link
    heading_divs = soup.find_all("div", attrs={"class": lambda c: c and "cmty-category-cell-heading" in c})
    print(f"🔍 Found {len(heading_divs)} category cell headings")
    
    for heading_div in heading_divs:
        # Look for the cmty-full-cell-link within this heading
        link_tag = heading_div.find("a", class_="cmty-full-cell-link")
        
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            if not href.startswith("http"):
                full_url = BASE_URL + href
            else:
                full_url = href
            
            # Get the title from the category cell title div for better identification
            title_div = heading_div.find("div", class_="cmty-category-cell-title")
            link_text = title_div.get_text(strip=True) if title_div else "Unknown"
            
            print(f"   🔗 Found subforum: {link_text} -> {full_url}")
            
            # Filter out the current page URL and ensure it's a valid community link
            if full_url != page_url and "/community/c" in full_url:
                # Additional check: ensure this isn't a navigation link
                if not any(skip in link_text.lower() for skip in ["back to", "parent", "home", "main"]):
                    sub_links.add(full_url)
                    print(f"   ✅ Added subforum: {link_text}")
                else:
                    print(f"   ⚠️  Skipped navigation link: {link_text}")
            else:
                print(f"   ⚠️  Skipped invalid or current page link: {full_url}")
    
    # Alternative approach: Look for the specific RGB color pattern
    if not sub_links:
        print("🔄 No subforums found with primary method, trying RGB color approach...")
        rgb_divs = soup.find_all("div", attrs={"style": lambda s: s and "rgb(53, 108, 181)" in s})
        print(f"   🎨 Found {len(rgb_divs)} divs with the specific RGB color")
        
        for rgb_div in rgb_divs:
            link_tag = rgb_div.find("a", class_="cmty-full-cell-link")
            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                full_url = BASE_URL + href if not href.startswith("http") else href
                
                title_div = rgb_div.find("div", class_="cmty-category-cell-title")
                link_text = title_div.get_text(strip=True) if title_div else "Unknown"
                
                if full_url != page_url and "/community/c" in full_url:
                    sub_links.add(full_url)
                    print(f"   ✅ Added via RGB method: {link_text}")
    
    # If we still haven't found any subforums, check if this is a direct post page
    if not sub_links:
        print("🔄 No subforums found, checking if this is a direct post page...")
        post_blocks = soup.find_all("div", attrs={"class": lambda x: x and "cmty-view-posts-item" in x})
        if post_blocks:
            print(f"   📝 Found {len(post_blocks)} posts directly on this page")
            print("   💡 This appears to be a direct post page, not a subforum container")
        else:
            print("   ❌ No posts found either - this might be an empty or differently structured page")
    
    print(f"📋 Final subforum count: {len(sub_links)}")
    return list(sub_links)

def get_problems_from_page(page_url, driver):
    driver.get(page_url)
    time.sleep(2)  # Give time for page to load

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

        problem_text = get_latex_aware_text(text_div)
        word_count = len(problem_text.split())
        if word_count < 2 or (word_count < 3 and "round" in problem_text.lower()):
            continue

        if problem_text:
            problems.append({
                "text": problem_text,
                "link": topic_link
            })

    return problems

def get_latex_aware_text(element):
    fragments = []

    def walk(node):
        if node.name == "img" and any(cls in node.get("class", []) for cls in ["latex", "latexcenter"]):
            alt = node.get("alt", "")
            if alt:
                # Don't strip the alt text - preserve exactly as is, including punctuation
                fragments.append(alt)
        elif node.name is None:
            # This is a text node - preserve it exactly as is
            text = str(node)
            if text:
                fragments.append(text)
        elif node.name in ["br"]:
            fragments.append("\n")
        else:
            for child in node.children:
                walk(child)

    walk(element)
    
    # Join all fragments and clean up whitespace while preserving punctuation
    result = "".join(fragments)
    
    # Clean up excessive whitespace but preserve single spaces and punctuation
    import re
    # Replace multiple whitespace with single space, but preserve structure
    result = re.sub(r'\s+', ' ', result)
    
    # Clean up spaces around punctuation - but be careful not to remove punctuation
    # Fix spaces before punctuation
    result = re.sub(r'\s+([,.!?;:])', r'\1', result)
    # Fix spaces after punctuation (ensure single space)
    result = re.sub(r'([,.!?;:])\s+', r'\1 ', result)
    
    return result.strip()

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

def get_sources_from_page(page_url, driver, year, comp_name, subforum_name=""):
    driver.get(page_url)
    time.sleep(2)
    
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    if not subforum_name:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Try multiple ways to get the subforum name
        title_selectors = [
            "div.cmty-category-cell-title",
            "div.cmty-category-cell-heading",
            "h1",
            "title"
        ]
        
        for selector in title_selectors:
            title_div = soup.select_one(selector)
            if title_div:
                subforum_name = title_div.get_text(strip=True)
                break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    post_blocks = soup.find_all("div", attrs={"class": lambda x: x and "cmty-view-posts-item" in x})

    current_test_name = subforum_name or ""
    link_source_map = {}

    for post in post_blocks:
        text_div = post.find("div", class_="cmty-view-post-item-text")
        if not text_div:
            continue
        text = text_div.get_text(strip=True)

        # If this text looks like a source header and post has no link, update current test name
        if is_source_block(text) and not post.find("a"):
            current_test_name = text
            continue

        label_div = post.find("div", class_="cmty-view-post-item-label")
        prob_number = label_div.get_text(strip=True) if label_div else "?"

        link_div = post.find("div", class_="cmty-view-post-topic-link")
        if not link_div:
            continue
        a_tag = link_div.find("a")
        if not a_tag or not a_tag.get("href"):
            continue
        topic_link = a_tag["href"]
        if not topic_link.startswith("http"):
            topic_link = BASE_URL + topic_link

        # Clean test name to remove words like round, test, team
        test_clean = re.sub(r"\b(round|test|team)\b", "", current_test_name, flags=re.I).strip()

        if test_clean:
            full_source = f"{comp_name} {year} {test_clean} #{prob_number}"
        else:
            full_source = f"{comp_name} {year} #{prob_number}"

        link_source_map[topic_link] = full_source

    return link_source_map

def extract_year_from_url(url):
    match = re.search(r"_(\d{4})", url)
    return match.group(1) if match else "unknown"

if __name__ == "__main__":
    print("🔍 Launching browser...")
    options = Options()
    # options.add_argument("--headless")  # Uncomment for headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    all_problems = []

    try:
        print(f"📂 Fetching {COMP_NAME} year links...")
        year_links = get_year_links(COMP_LINK)
        print(f"✅ Found {len(year_links)} contest years")

        for year_url in year_links:
            print(f"\n📄 Scraping problems from: {year_url}")
            year_id = extract_year_from_url(year_url)

            # Initialize empty collections
            problems = []
            link_source_map = {}

            # First, check for sub-forums
            print("🔁 Checking for sub-forums...")
            sub_links = get_sub_forum_links(year_url, driver)
            
            if sub_links:
                print(f"✅ Found {len(sub_links)} sub-forums - processing subforums only")
                for sub_url in sub_links:
                    print(f"↳ Processing sub-forum: {sub_url}")
                    # Get problems from subforum
                    sub_problems = get_problems_from_page(sub_url, driver)
                    problems.extend(sub_problems)
                    print(f"   📝 Found {len(sub_problems)} problems in this subforum")
                    
                    # Get source mapping from subforum
                    sub_source_map = get_sources_from_page(sub_url, driver, year_id, COMP_NAME)
                    link_source_map.update(sub_source_map)
                    print(f"   🏷️  Generated {len(sub_source_map)} source mappings")
            else:
                print("⚠️  No sub-forums found - processing main page post blocks")
                # Only process main page if no subforums exist
                link_source_map = get_sources_from_page(year_url, driver, year_id, COMP_NAME)
                problems = get_problems_from_page(year_url, driver)

            print(f"🧮 Total problems found: {len(problems)}")

            # Process problems without scraping solutions
            for i, prob in enumerate(problems, 1):
                source = link_source_map.get(prob["link"], f"{COMP_NAME} {year_id} unknown")

                all_problems.append({
                    "text": prob["text"],
                    "link": prob["link"],
                    "source": source
                })

                # Print every 10 problems for checking
                if i % 10 == 0:
                    print(f"   Problem {i}: {prob['link']}")
                    print(f"   Source: {source}")

        output_file = f"{COMP_NAME}_problems_only.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_problems, f, indent=2, ensure_ascii=False)

        print(f"\n✅ All problems saved to {output_file}")
        print(f"📊 Total problems scraped: {len(all_problems)}")

    finally:
        driver.quit()
        print("🚪 Browser closed.")