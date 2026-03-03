import requests
from bs4 import BeautifulSoup
import time
import random

# Use the URL found
base_url = "http://www.xbiqugu.la/0/844/"
test_chapter_url = "http://www.xbiqugu.la/0/844/326886.html" # Assuming first chapter

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_chapter(url):
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8' # xbiqugu usually uses utf-8 or gb18030
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Extract content
            # Usually in <div id="content">
            content_div = soup.find('div', id='content')
            if content_div:
                text = content_div.get_text(separator="\n").strip()
                # Clean up some common ads
                lines = [line for line in text.split('\n') if "笔趣阁" not in line and "http" not in line]
                return "\n".join(lines)
            else:
                return "Error: Content not found"
        else:
            return f"Error: Status {resp.status_code}"
    except Exception as e:
        return f"Error: {e}"

# First, get the chapter list
print("Fetching chapter list...")
try:
    resp = requests.get(base_url, headers=headers, timeout=10)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Check encoding if title is garbage
    print(f"Page Title: {soup.title.string}")
    
    # Get all links in #list dl dd a
    links = soup.select("#list dl dd a")
    print(f"Found {len(links)} chapters.")
    
    if len(links) > 0:
        # Test first chapter
        first_chap = links[0]
        full_url = "http://www.xbiqugu.la" + first_chap.get('href')
        print(f"Testing first chapter: {first_chap.get_text()} -> {full_url}")
        
        content = get_chapter(full_url)
        print("--- Content Preview ---")
        print(content[:200])
        print("-----------------------")
        
except Exception as e:
    print(f"Error fetching list: {e}")
