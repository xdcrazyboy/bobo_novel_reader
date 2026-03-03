from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. Try generic search for character name
        search_query = "古月方源 笔趣阁 目录"
        print(f"Searching Bing for: {search_query}")
        try:
            page.goto(f"https://www.bing.com/search?q={search_query}", timeout=15000)
            page.wait_for_load_state("domcontentloaded")
            links = page.query_selector_all("h2 a")
            
            for link in links[:5]:
                href = link.get_attribute("href")
                print(f"Checking Bing Result: {href}")
                try:
                    page.goto(href, timeout=10000)
                    if "章" in page.content() and ("方源" in page.content() or "蛊" in page.content()):
                        print(f"!!! FOUND POTENTIAL SITE: {href}")
                        # Print first few chapters to verify
                        chapters = page.query_selector_all("a")
                        valid_count = 0
                        for c in chapters:
                            if "第" in c.inner_text() and "章" in c.inner_text():
                                valid_count += 1
                        print(f"    - Valid chapter links found: {valid_count}")
                        if valid_count > 20:
                             print(f"    - HIGHLY LIKELY MATCH!")
                             browser.close()
                             return
                except Exception as e:
                    print(f"    - Failed to load {href}: {e}")
                    
        except Exception as e:
            print(f"Bing search failed: {e}")

        # 2. Hardcoded sites search (simulate user behavior)
        sites = [
            "https://www.xbiquge.la",
            "https://www.biquge.co",
            "https://www.bqg.org",
            "https://www.bbiquge.net"
        ]
        
        for site in sites:
            print(f"Checking Site: {site}")
            try:
                # Some sites have search box
                page.goto(site, timeout=10000)
                # Try to find input
                inputs = page.query_selector_all("input")
                search_input = None
                for inp in inputs:
                    # simplistic check for search box
                    if inp.is_visible():
                        search_input = inp
                        break
                
                if search_input:
                    print(f"  - Found input box on {site}, typing '蛊真人'...")
                    search_input.fill("蛊真人")
                    search_input.press("Enter")
                    page.wait_for_load_state("domcontentloaded")
                    
                    if "方源" in page.content():
                         print(f"!!! FOUND ON {site}")
                         print(f"Current URL: {page.url}")
                         browser.close()
                         return
                else:
                    print(f"  - No obvious search input found.")

            except Exception as e:
                print(f"  - Error checking {site}: {e}")

        browser.close()

if __name__ == "__main__":
    run()
