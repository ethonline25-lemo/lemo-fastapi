import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.web_scrapper import web_scrapper
from helpers.embedder import generate_embedding
from helpers.redis_functions import store_page_vector, get_relevant_content


def current_page_context(url: str, query: str):
    try:
        print(f"[LOG] Starting current_page_context for URL: {url}")
        print(f"[LOG] Query: {query}")
        
        print("[LOG] Scraping webpage content...")
        chunks = web_scrapper(url, full_page=True)
        
        if not chunks or len(chunks) == 0:
            print("[WARNING] No chunks retrieved from webpage")
            return []
        
        print(f"[LOG] Retrieved {len(chunks)} chunks from webpage")
        
        for i, chunk in enumerate(chunks):
            try:
                print(f"[LOG] Processing chunk {i+1}/{len(chunks)}")
                embedding = generate_embedding(chunk)
                print(f"[LOG] Generated embedding for chunk {i+1}")
                result = store_page_vector(url, chunk, embedding)
                print(f"[LOG] Stored chunk {i+1}: {result}")
            except Exception as e:
                print(f"[ERROR] Failed to process chunk {i+1}: {e}")
                continue
        
        print("[LOG] Generating query embedding...")
        query_embedding = generate_embedding(query)
        print("[LOG] Query embedding generated")
        
        print("[LOG] Searching for relevant content...")
        content = get_relevant_content(url, query_embedding, top_k=5)
        print(f"[LOG] Found {len(content)} relevant content chunks")
        
        return content
    
    except Exception as e:
        print(f"[ERROR] Error in current_page_context: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("[INFO] Running current_page_context test")
    content = current_page_context("https://allensolly.abfrl.in/p/men-blue-textured-polo-neck-t-shirt-39871258.html", "What is this product about?")
    print("[RESULT] Relevant content:")
    print(content)