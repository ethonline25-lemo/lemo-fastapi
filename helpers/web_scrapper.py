import requests
from bs4 import BeautifulSoup

def web_scrapper(url: str):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract h tags and p tags in order
    all_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])
    
    # Build a single chunk up to 900 characters
    chunk = ""
    for tag in all_tags:
        text = tag.get_text(strip=True)
        if text:
            # Add space separator if chunk is not empty
            potential_addition = (" " + text) if chunk else text
            
            # Check if adding this text would exceed 900 characters
            if len(chunk + potential_addition) > 900:
                break
            
            chunk += potential_addition
    
    return chunk