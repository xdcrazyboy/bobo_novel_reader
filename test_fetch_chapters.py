import requests
from bs4 import BeautifulSoup

url = "https://m.biqugf.com/book/14027"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'utf-8' # or response.apparent_encoding
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Print title
        print(f"Title: {soup.title.string}")
        
        # Try to find chapter links. The structure depends on the specific site.
        # Common patterns: <ul class="chapter"> <li> <a href="...">
        # or just <a> tags in a specific div.
        
        links = soup.find_all('a')
        count = 0
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if href and 'chapter' in href or 'book' in href or href.endswith('.html'):
                # Basic filtering to see if we get chapter links
                print(f"Link: {text} -> {href}")
                count += 1
                if count > 10:
                    break
    else:
        print(f"Failed with status code: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")
