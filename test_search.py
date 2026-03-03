import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def test_search(name):
    # xbiqugu.la search using waps.php (HTTP)
    search_url = "http://www.xbiqugu.la/modules/article/waps.php"
    payload = {'searchkey': name}
    
    print(f"Searching for '{name}' at {search_url}...")
    try:
        # Use verify=False due to cert issues
        resp = requests.post(search_url, data=payload, headers=headers, timeout=15, verify=False)
        print(f"Status Code: {resp.status_code}")
        print(f"Final URL: {resp.url}")
        
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Check for results
        results = soup.select(".grid tr")[1:]
        if results:
            print(f"Found {len(results)} results.")
            for r in results:
                cols = r.find_all('td')
                if len(cols) >= 1:
                    title_a = cols[0].find('a')
                    print(f"Result: {title_a.get_text()} by {cols[2].get_text()} - {urljoin(search_url, title_a.get('href'))}")
        elif soup.find('div', id='info'):
            print(f"Direct match found: {soup.find('div', id='info').find('h1').get_text()}")
        else:
            print("No results found.")
            # Some sites might use different classes for search results
            print(resp.text[:1000])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search("斗破苍穹")
