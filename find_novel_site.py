from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. Search on Bing
        search_url = "https://www.bing.com/search?q=蛊真人+笔趣阁+目录"
        print(f"Searching: {search_url}")
        page.goto(search_url)
        page.wait_for_load_state("networkidle")
        
        # 2. Extract links
        # Bing results are usually in <h2><a href="...">
        links = page.query_selector_all("h2 a")
        candidate_urls = []
        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                candidate_urls.append(href)
        
        print(f"Found {len(candidate_urls)} candidates.")
        
        # 3. Check each candidate
        target_url = None
        for url in candidate_urls[:5]: # Check first 5
            print(f"Checking {url}...")
            try:
                page.goto(url, timeout=15000)
                page.wait_for_load_state("domcontentloaded")
                
                title = page.title()
                content = page.content()
                
                # Check for key elements
                if "蛊真人" in title and ("方源" in content or "古月" in content):
                    # Check if it has a list of chapters
                    chapter_links = page.query_selector_all("a")
                    # Count links that look like chapters (contain numbers or "章" or "节")
                    valid_chapters = 0
                    for cl in chapter_links:
                        txt = cl.inner_text()
                        if "章" in txt or "节" in txt:
                            valid_chapters += 1
                    
                    if valid_chapters > 50:
                        print(f"SUCCESS: Found valid site at {url} with {valid_chapters} chapters.")
                        target_url = url
                        break
                    else:
                        print(f"  - Not enough chapters ({valid_chapters})")
                else:
                    print(f"  - Title or content mismatch. Title: {title}")
                    
            except Exception as e:
                print(f"  - Error: {e}")
        
        if target_url:
            print(f"TARGET_URL_FOUND: {target_url}")
        else:
            print("TARGET_URL_NOT_FOUND")

        browser.close()

if __name__ == "__main__":
    run()
