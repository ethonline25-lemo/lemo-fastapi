import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from helpers.get_product_urls import browser
from helpers.web_scrapper import web_scrapper
from helpers.embedder import generate_embedding
from helpers.redis_functions import store_vector
from helpers.redis_functions import search_similar


def product_recommendation(domain: str, user_query: str):
    print(f"[LOG] Starting product recommendation for query: '{user_query}' on domain: '{domain}'")
    
    list_of_products = browser(user_query, domain, 4)["urls"]
    print(f"[LOG] Found {len(list_of_products)} products from browser")
    
    for idx, product_url in enumerate(list_of_products, 1):
        print(f"[LOG] Processing product {idx}/{len(list_of_products)}: {product_url}")
        chunks = web_scrapper(product_url)
        print(f"[LOG] Extracted {len(chunks)} chunks from {product_url}")
        
        for chunk_idx, chunk in enumerate(chunks, 1):
            print(f"[LOG] Generating embedding for chunk {chunk_idx}/{len(chunks)}")
            embedding = generate_embedding(chunk)
            print(f"[LOG] Storing vector for {product_url}")
            store_vector(product_url, embedding)
    
    print(f"[LOG] Generating embedding for user query: '{user_query}'")
    query_embedding = generate_embedding(user_query)
    
    print(f"[LOG] Searching for similar products (top 10)")
    similar_products = search_similar(query_embedding, 10)
    print(f"[LOG] Found {len(similar_products)} similar products")
    
    similar_products_urls = set([product[0] for product in similar_products])
    print(f"[LOG] Unique product URLs: {len(similar_products_urls)}")
    print(f"[LOG] Recommendation complete. Returning {len(similar_products_urls)} unique products")
    
    return similar_products_urls

result = product_recommendation("allensolly.abfrl.in", "Blue Jeans for men")
print(result)