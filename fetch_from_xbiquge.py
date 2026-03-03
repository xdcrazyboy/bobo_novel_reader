from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        
        url = "https://www.xbiquge.la"
        print(f"Accessing {url}...")
        try:
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            
            # Find search input
            # Usually input[name="wd"] or similar
            search_input = page.query_selector("input[id='wd']") 
            if not search_input:
                 search_input = page.query_selector("input[name='searchkey']") # common pattern
            
            if search_input:
                print("Found search input, searching for '蛊真人'...")
                search_input.fill("蛊真人")
                search_input.press("Enter")
                
                # Wait for navigation
                page.wait_for_load_state("domcontentloaded")
                
                # Check if we are on a search result page or book page
                # If result page, click first link
                # xbiquge.la often redirects to book page if exact match, or shows list
                
                print(f"Current URL: {page.url}")
                print(f"Page Title: {page.title()}")
                
                # Check for chapter list
                chapters = page.query_selector_all("#list dd a") # Common structure for xbiquge
                
                if len(chapters) > 0:
                    print(f"Found {len(chapters)} chapters!")
                    with open("chapter_list.txt", "w", encoding="utf-8") as f:
                        for i, ch in enumerate(chapters):
                            title = ch.inner_text()
                            href = ch.get_attribute("href")
                            # xbiquge often uses relative paths
                            if not href.startswith("http"):
                                href = "https://www.xbiquge.la" + href
                            f.write(f"{title}|{href}\n")
                            if i < 5:
                                print(f"  {title} -> {href}")
                    print("Saved chapter list to chapter_list.txt")
                else:
                    print("No chapters found directly. Maybe need to click a result?")
                    # Check for search results
                    results = page.query_selector_all(".result-game-item-title-link") # generic selector guess
                    if not results:
                        results = page.query_selector_all("td a") # another common one
                    
                    if results:
                        print(f"Found {len(results)} search results.")
                        for r in results[:3]:
                            print(f"  {r.inner_text()} -> {r.get_attribute('href')}")
            else:
                print("Search input not found!")

        except Exception as e:
            print(f"Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()
