import requests
from bs4 import BeautifulSoup
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from urllib.parse import quote, urljoin

class NovelDownloader:
    def __init__(self, headers=None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Updated to working search endpoint found via debugging
        self.base_search_url = "http://www.xbiqugu.la/modules/article/waps.php"
        self.site_domain = "http://www.xbiqugu.la"

    def search_novel(self, name):
        """Search for a novel and return a list of (title, author, url)"""
        try:
            payload = {'searchkey': name}
            # Using verify=False and http to avoid SSL/Cert issues common with mirrors
            resp = requests.post(self.base_search_url, data=payload, headers=self.headers, timeout=15)
            resp.encoding = 'utf-8'
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            
            # Check for grid table in the search results
            table = soup.find('table', class_='grid')
            if table:
                rows = table.find_all('tr')[1:] # Skip header
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        title_a = cols[0].find('a')
                        if title_a:
                            title = title_a.get_text().strip()
                            url = urljoin(self.site_domain, title_a.get('href'))
                            author = cols[2].get_text().strip()
                            results.append({'title': title, 'author': author, 'url': url})
            
            # Check if redirected directly to the book page (common for exact matches)
            elif soup.find('div', id='info'):
                title = soup.find('div', id='info').find('h1').get_text().strip()
                author_p = soup.find('div', id='info').find('p')
                author = author_p.get_text().replace('作\xa0\xa0\xa0\xa0者：', '').strip() if author_p else "未知"
                results.append({'title': title, 'author': author, 'url': resp.url})
            
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_chapter_list(self, book_url):
        """Get list of (title, url) for all chapters"""
        try:
            resp = requests.get(book_url, headers=self.headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            links = soup.select("#list dl dd a")
            chapters = []
            for i, link in enumerate(links):
                title = link.get_text()
                href = link.get('href')
                full_url = urljoin(book_url, href)
                chapters.append({'idx': i, 'title': title, 'url': full_url})
            return chapters
        except Exception as e:
            print(f"Get TOC error: {e}")
            return []

    def clean_text(self, text):
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove common ads and site names
            if any(ad in line.lower() for ad in ["最新网址", "xbiqugu", "笔趣阁", "chaptererror", "本章未完"]):
                continue
            cleaned_lines.append(line)
        return "\n\n".join(cleaned_lines)

    def download_chapter(self, chapter_info, output_dir):
        idx = chapter_info['idx']
        title = chapter_info['title']
        url = chapter_info['url']
        filename = os.path.join(output_dir, f"{idx:05d}.txt")
        
        if os.path.exists(filename):
            return True

        try:
            for _ in range(3): # Retry 3 times
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code == 200:
                    resp.encoding = 'utf-8'
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    content_div = soup.find('div', id='content')
                    if content_div:
                        # Some sites put ads in script or other tags inside content
                        for s in content_div(['script', 'style', 'div']):
                            s.decompose()
                            
                        content = content_div.get_text(separator="\n")
                        cleaned = self.clean_text(content)
                        
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(f"{title}\n\n{cleaned}\n\n")
                        return True
                time.sleep(1)
            return False
        except:
            return False

    def start_download(self, book_info, progress_callback=None):
        """
        Download all chapters and merge into one TXT.
        book_info: {'title', 'author', 'url'}
        progress_callback: function(current, total, status_text)
        """
        title = book_info['title']
        author = book_info['author']
        url = book_info['url']
        
        # Create temp dir for chapters
        temp_dir = os.path.join(os.getcwd(), f"temp_{int(time.time())}")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        if progress_callback: progress_callback(0, 1, "正在获取目录...")
        chapters = self.get_chapter_list(url)
        if not chapters:
            return None

        total = len(chapters)
        completed = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.download_chapter, ch, temp_dir): ch for ch in chapters}
            for future in as_completed(futures):
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, f"正在下载: {futures[future]['title']}")
        
        # Merge
        final_filename = f"{title}_{author}.txt"
        final_path = os.path.abspath(final_filename)
        
        if progress_callback: progress_callback(total, total, "正在合并文件...")
        with open(final_path, "w", encoding="utf-8") as outfile:
            outfile.write(f"《{title}》\n作者：{author}\n\n")
            for i in range(total):
                ch_file = os.path.join(temp_dir, f"{i:05d}.txt")
                if os.path.exists(ch_file):
                    with open(ch_file, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                        outfile.write("\n" + "="*30 + "\n\n")
        
        # Cleanup temp
        import shutil
        shutil.rmtree(temp_dir)
        
        return final_path

if __name__ == "__main__":
    # Test search
    dl = NovelDownloader()
    print("Searching...")
    results = dl.search_novel("蛊真人")
    for r in results:
        print(f"Found: {r['title']} - {r['author']} - {r['url']}")
