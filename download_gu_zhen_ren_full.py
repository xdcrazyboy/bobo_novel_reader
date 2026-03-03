import requests
from bs4 import BeautifulSoup
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

BASE_URL = "http://www.xbiqugu.la/0/844/"
OUTPUT_DIR = "chapters"
FINAL_FILE = "蛊真人_全文.txt"
MAX_WORKERS = 10

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def clean_text(text):
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "最新网址" in line or "xbiqugu.la" in line or "笔趣阁" in line:
            continue
        cleaned_lines.append("    " + line) # Add indentation
    return "\n\n".join(cleaned_lines)

def download_chapter(chapter_info):
    idx, title, url = chapter_info
    filename = os.path.join(OUTPUT_DIR, f"{idx:04d}.txt")
    
    if os.path.exists(filename):
        return f"Skipped {title}"

    try:
        # Retry logic
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    resp.encoding = 'utf-8'
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    content_div = soup.find('div', id='content')
                    
                    if content_div:
                        content = content_div.get_text(separator="\n")
                        cleaned_content = clean_text(content)
                        
                        full_text = f"{title}\n\n{cleaned_content}\n\n"
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(full_text)
                        return f"Downloaded {title}"
                    else:
                        # Sometimes content is empty or protected?
                        return f"Failed {title}: No content div"
                else:
                    time.sleep(1)
            except requests.RequestException:
                time.sleep(2)
        return f"Failed {title} after retries"
        
    except Exception as e:
        return f"Error {title}: {e}"

def main():
    print("Fetching chapter list...")
    try:
        resp = requests.get(BASE_URL, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Select all chapter links
        links = soup.select("#list dl dd a")
        chapters = []
        for i, link in enumerate(links):
            title = link.get_text()
            href = link.get('href')
            if not href.startswith("http"):
                href = "http://www.xbiqugu.la" + href
            chapters.append((i, title, href))
            
        print(f"Found {len(chapters)} chapters. Starting download...")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_chapter = {executor.submit(download_chapter, ch): ch for ch in chapters}
            
            completed = 0
            total = len(chapters)
            
            for future in as_completed(future_to_chapter):
                completed += 1
                result = future.result()
                if completed % 50 == 0:
                    print(f"[{completed}/{total}] {result}")

        print("Download complete. Merging files...")
        
        with open(FINAL_FILE, "w", encoding="utf-8") as outfile:
            outfile.write("《蛊真人》\n作者：蛊真人\n来源：网络爬取\n\n")
            for i in range(len(chapters)):
                filename = os.path.join(OUTPUT_DIR, f"{i:04d}.txt")
                if os.path.exists(filename):
                    with open(filename, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                        outfile.write("\n" + "="*20 + "\n\n")
                else:
                    outfile.write(f"\n[缺失章节 {i}: {chapters[i][1]}]\n\n")
        
        print(f"All done! Saved to {FINAL_FILE}")
        
    except Exception as e:
        print(f"Main error: {e}")

if __name__ == "__main__":
    main()
