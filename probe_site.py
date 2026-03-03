from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 尝试移动版链接
        url = "https://m.bqg9527.cc/book/103812/"
        print(f"Accessing {url}...")
        
        try:
            page.goto(url, timeout=30000)
            print(f"Title: {page.title()}")
            
            # 尝试获取章节列表
            # 通常在 #list, .list, 或 .chapter-list 中
            # 这里先打印页面结构的一小部分来分析，或者尝试直接定位链接
            
            links = page.query_selector_all('dd a') # 笔趣阁常见结构：<div id="list"><dl><dd><a>...
            
            if not links:
                links = page.query_selector_all('.chapter a') # 另一种常见结构
            
            print(f"Found {len(links)} links.")
            
            for i, link in enumerate(links[:5]):
                print(f"Chapter {i}: {link.inner_text()} -> {link.get_attribute('href')}")
                
        except Exception as e:
            print(f"Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()
