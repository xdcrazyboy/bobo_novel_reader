import re
import os
import json
import hashlib

class NovelParser:
    CHAPTER_PATTERNS = [
        r'^\s*第[一二三四五六七八九十百千万零\d]+[章节回节卷].*',
        r'^\s*序[:：\s].*',
        r'^\s*前言.*',
        r'^\s*楔子.*',
        r'^\s*引子.*'
    ]

    def __init__(self, file_path, cache_dir=None):
        self.file_path = file_path
        self.chapters = [] # List of {'title', 'start', 'end'}
        self.encoding = 'utf-8'
        self.cache_dir = cache_dir or os.path.dirname(os.path.abspath(file_path))
        
    def _get_cache_path(self):
        # Generate a unique cache name based on file path and size
        # Added a version prefix to invalidate old incorrect caches
        file_stats = os.stat(self.file_path)
        unique_str = f"v2_{self.file_path}_{file_stats.st_size}_{file_stats.st_mtime}"
        file_hash = hashlib.md5(unique_str.encode()).hexdigest()
        return os.path.join(self.cache_dir, f".reader_cache_{file_hash}.json")

    def parse(self):
        cache_path = self._get_cache_path()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    self.chapters = json.load(f)
                if self.chapters and len(self.chapters) > 10: # Basic sanity check
                    return self.chapters
            except:
                pass

        self.chapters = []
        # Compile patterns for strings to avoid byte-regex complexity
        patterns = [re.compile(p) for p in self.CHAPTER_PATTERNS]
        
        try:
            with open(self.file_path, 'rb') as f:
                last_pos = 0
                last_title = "开始"
                
                # We'll read line by line. For each line, we decode only the first few bytes 
                # to check if it's a potential heading. This is very fast.
                while True:
                    pos = f.tell()
                    line_bytes = f.readline()
                    if not line_bytes:
                        break
                    
                    # Skip empty or too long lines (headings are usually short)
                    if not line_bytes.strip() or len(line_bytes) > 300:
                        continue
                        
                    try:
                        # Decode the line to check against patterns
                        line_str = line_bytes.decode('utf-8', errors='ignore').strip()
                        
                        is_match = False
                        for p in patterns:
                            if p.match(line_str):
                                is_match = True
                                break
                        
                        if is_match:
                            if last_pos != pos:
                                self.chapters.append({
                                    'title': last_title,
                                    'start': last_pos,
                                    'end': pos
                                })
                            last_title = line_str
                            last_pos = pos
                    except:
                        continue
                
                # Add the last chapter
                self.chapters.append({
                    'title': last_title,
                    'start': last_pos,
                    'end': f.tell()
                })
        except Exception as e:
            print(f"Error parsing: {e}")
        
        if not self.chapters or (len(self.chapters) == 1 and self.chapters[0]['title'] == "开始"):
             self.chapters = [{
                'title': "全书",
                'start': 0,
                'end': os.path.getsize(self.file_path)
            }]
        
        # Save to cache
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.chapters, f, ensure_ascii=False)
        except:
            pass
            
        return self.chapters

    def get_chapter_content(self, index):
        if 0 <= index < len(self.chapters):
            ch = self.chapters[index]
            with open(self.file_path, 'r', encoding=self.encoding, errors='ignore') as f:
                f.seek(ch['start'])
                content = f.read(ch['end'] - ch['start'])
                return content
        return ""

if __name__ == "__main__":
    # Test with the downloaded novel
    test_file = "蛊真人_全文.txt"
    if os.path.exists(test_file):
        parser = NovelParser(test_file)
        chapters = parser.parse()
        print(f"Parsed {len(chapters)} chapters.")
        for i in range(min(5, len(chapters))):
            print(f"Chapter {i}: {chapters[i]['title']}")
    else:
        print(f"File {test_file} not found.")
