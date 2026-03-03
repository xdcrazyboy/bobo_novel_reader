from downloader import NovelDownloader
import os

def main():
    dl = NovelDownloader()
    print("Searching for '斗破苍穹'...")
    results = dl.search_novel("斗破苍穹")
    
    if not results:
        print("Search failed!")
        return
        
    # Find the best match (usually the first one by 天蚕土豆)
    book = None
    for r in results:
        if r['title'] == "斗破苍穹" and "天蚕土豆" in r['author']:
            book = r
            break
    
    if not book:
        book = results[0]
        
    print(f"Found book: {book['title']} by {book['author']} at {book['url']}")
    
    # Download first 5 chapters only for speed in this test, or full if requested?
    # User said "实际下载这个到书架看看", let's download a small portion first to verify, 
    # but the user might expect the whole thing. 
    # Actually, for "斗破苍穹" it's huge. Let's try to download a reasonable number or full.
    # The start_download method downloads all. 
    # I'll modify downloader.py slightly to allow a limit for testing, or just go for it.
    
    # Actually, I'll just use the start_download as is. 
    # It might take a while, but it's the most thorough test.
    
    def progress(current, total, status):
        if current % 100 == 0 or current == total:
            print(f"[{current}/{total}] {status}")

    print("Starting download...")
    final_path = dl.start_download(book, progress)
    
    if final_path and os.path.exists(final_path):
        print(f"Download successful! File saved at: {final_path}")
    else:
        print("Download failed!")

if __name__ == "__main__":
    main()
