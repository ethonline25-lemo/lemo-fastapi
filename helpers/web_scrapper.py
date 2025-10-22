import requests
from bs4 import BeautifulSoup

def web_scrapper(url: str, full_page: bool = False):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        if full_page:
            data = soup.get_text().strip()
            if not data:
                print("[WARNING] No text content found on the page")
                return []
            
            # Filter out excessive whitespace
            data = ' '.join(data.split())
            
            chunks = [data[i:i+1000] for i in range(0, len(data), 1000)]
            # Filter out empty or very small chunks
            chunks = [chunk for chunk in chunks if len(chunk.strip()) > 20]
            return chunks
            
        # Extract h tags and p tags in order
        all_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])
        
        # Build a single chunk up to 1000 characters (matching embedder.py truncation limit)
        chunk = ""
        for tag in all_tags:
            text = tag.get_text(strip=True)
            if text:
                # Add space separator if chunk is not empty
                if chunk:
                    potential_addition = chunk + " " + text
                else:
                    potential_addition = text
                
                # Check if adding this text would exceed 1000 characters
                if len(potential_addition) > 1000:
                    break
                
                chunk = potential_addition
        
        return chunk if chunk else []
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to scrape URL {url}: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in web_scrapper: {e}")
        raise