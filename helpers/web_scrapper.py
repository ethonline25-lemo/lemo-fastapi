import requests
from bs4 import BeautifulSoup
import time

def web_scrapper(url: str, full_page: bool = False):
    try:
        # Check for non-scrapable URLs first
        non_scrapable_schemes = ['chrome://', 'chrome-extension://', 'about:', 'file://', 'data:', 'javascript:', 'edge://', 'brave://']
        is_non_scrapable = any(url.lower().startswith(scheme) for scheme in non_scrapable_schemes)
        
        if is_non_scrapable:
            print(f"\n{'='*80}")
            print(f"[SCRAPER] ✗ SKIPPED: Cannot scrape browser-internal URL: {url}")
            print(f"[SCRAPER] This is a {url.split(':')[0]}:// page - not a real website")
            print(f"{'='*80}\n")
            return []
        
        # AGGRESSIVE headers to bypass bot detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        print(f"\n{'='*80}")
        print(f"[SCRAPER] Starting scrape for: {url}")
        print(f"{'='*80}")
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        print(f"[SCRAPER] Response Status: {response.status_code}")
        print(f"[SCRAPER] Response Length: {len(response.text)} characters")
        print(f"[SCRAPER] Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        if full_page:
            print(f"[SCRAPER] Extracting product information...")
            
            # EXTRACT KEY PRODUCT INFO FIRST
            product_data = []
            
            # Title extraction (multiple selectors)
            title_selectors = [
                {'id': 'productTitle'},
                {'class_': 'product-title'},
                {'class_': 'a-size-large'},
            ]
            title_found = False
            for selector in title_selectors:
                title = soup.find('span', selector) or soup.find('h1', selector)
                if title:
                    title_text = title.get_text(strip=True)
                    if title_text and len(title_text) > 10:
                        product_data.append(f"PRODUCT TITLE: {title_text}")
                        print(f"[SCRAPER] ✓ Found title: {title_text[:80]}...")
                        title_found = True
                        break
            
            if not title_found:
                print(f"[SCRAPER] ✗ No title found")
            
            # Price extraction (multiple strategies)
            price_found = False
            
            # Strategy 1: Find a-price span with whole number
            try:
                price_container = soup.find('span', {'class': 'a-price'})
                if price_container:
                    whole = price_container.find('span', {'class': 'a-price-whole'})
                    fraction = price_container.find('span', {'class': 'a-price-fraction'})
                    symbol = price_container.find('span', {'class': 'a-price-symbol'})
                    
                    if whole:
                        price_text = ''
                        if symbol:
                            price_text += symbol.get_text(strip=True)
                        price_text += whole.get_text(strip=True)
                        if fraction:
                            price_text += fraction.get_text(strip=True)
                        
                        if price_text and any(char.isdigit() for char in price_text):
                            product_data.append(f"PRICE: {price_text}")
                            print(f"[SCRAPER] ✓ Found price (Strategy 1): {price_text}")
                            price_found = True
            except Exception as e:
                print(f"[SCRAPER] Price Strategy 1 failed: {e}")
            
            # Strategy 2: Find any element with price-related text
            if not price_found:
                try:
                    # Look for elements containing currency symbols and numbers
                    import re
                    price_pattern = re.compile(r'[₹$€£]\s*[\d,]+\.?\d*')
                    
                    # Check common price containers
                    price_areas = soup.find_all(['span', 'div'], string=price_pattern)
                    for elem in price_areas[:5]:  # Check first 5 matches
                        price_text = elem.get_text(strip=True)
                        if price_pattern.search(price_text):
                            # Extract just the price part
                            match = price_pattern.search(price_text)
                            if match:
                                product_data.append(f"PRICE: {match.group()}")
                                print(f"[SCRAPER] ✓ Found price (Strategy 2): {match.group()}")
                                price_found = True
                                break
                except Exception as e:
                    print(f"[SCRAPER] Price Strategy 2 failed: {e}")
            
            # Strategy 3: Look in specific IDs
            if not price_found:
                price_ids = ['priceblock_ourprice', 'priceblock_dealprice', 'price', 'tp_price_block_total_price_ww']
                for price_id in price_ids:
                    price_elem = soup.find(id=price_id)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        if price_text and any(char.isdigit() for char in price_text):
                            product_data.append(f"PRICE: {price_text}")
                            print(f"[SCRAPER] ✓ Found price (Strategy 3 - {price_id}): {price_text}")
                            price_found = True
                            break
            
            if not price_found:
                print(f"[SCRAPER] ✗ No price found (tried all strategies)")
            
            # Discount extraction
            try:
                discount = soup.find('span', {'class': 'savingsPercentage'}) or soup.find('span', string=lambda x: x and '%' in x and 'off' in x.lower())
                if discount:
                    discount_text = discount.get_text(strip=True)
                    product_data.append(f"DISCOUNT: {discount_text}")
                    print(f"[SCRAPER] ✓ Found discount: {discount_text}")
            except Exception as e:
                print(f"[SCRAPER] Discount extraction failed: {e}")
            
            # MRP/Original Price
            try:
                mrp = soup.find('span', {'class': 'a-text-price'})
                if mrp:
                    mrp_text = mrp.get_text(strip=True)
                    if 'M.R.P' in mrp_text or '₹' in mrp_text:
                        product_data.append(f"MRP: {mrp_text}")
                        print(f"[SCRAPER] ✓ Found MRP: {mrp_text}")
            except Exception as e:
                print(f"[SCRAPER] MRP extraction failed: {e}")
            
            # Rating extraction
            rating = soup.find('span', {'class': 'a-icon-alt'})
            if rating:
                rating_text = rating.get_text(strip=True)
                product_data.append(f"RATING: {rating_text}")
                print(f"[SCRAPER] ✓ Found rating: {rating_text}")
            
            # Number of ratings
            try:
                rating_count = soup.find('span', {'id': 'acrCustomerReviewText'})
                if rating_count:
                    count_text = rating_count.get_text(strip=True)
                    product_data.append(f"REVIEWS: {count_text}")
                    print(f"[SCRAPER] ✓ Found review count: {count_text}")
            except Exception as e:
                print(f"[SCRAPER] Review count extraction failed: {e}")
            
            # Features/Description
            feature_bullets = soup.find('div', {'id': 'feature-bullets'})
            if feature_bullets:
                features = feature_bullets.get_text(strip=True)[:1000]
                product_data.append(f"FEATURES: {features}")
                print(f"[SCRAPER] ✓ Found features: {features[:150]}...")
            
            # Product description
            desc = soup.find('div', {'id': 'productDescription'})
            if desc:
                desc_text = desc.get_text(strip=True)[:800]
                product_data.append(f"DESCRIPTION: {desc_text}")
                print(f"[SCRAPER] ✓ Found description: {desc_text[:100]}...")
            
            # Availability
            try:
                availability = soup.find('div', {'id': 'availability'})
                if availability:
                    avail_text = availability.get_text(strip=True)
                    if avail_text:
                        product_data.append(f"AVAILABILITY: {avail_text}")
                        print(f"[SCRAPER] ✓ Found availability: {avail_text}")
            except Exception as e:
                print(f"[SCRAPER] Availability extraction failed: {e}")
            
            # Get ALL page text as fallback
            full_text = soup.get_text(separator=' ', strip=True)
            
            if not full_text or len(full_text) < 100:
                print(f"[SCRAPER] ✗✗✗ CRITICAL: Minimal text extracted ({len(full_text)} chars)")
                print(f"[SCRAPER] This likely means Amazon blocked the request")
                return []
            
            print(f"[SCRAPER] ✓ Full page text: {len(full_text)} characters")
            
            # Combine product data with full text
            if product_data:
                combined_text = ' | '.join(product_data) + ' | ' + full_text
                print(f"[SCRAPER] ✓ Combined with extracted product data")
            else:
                combined_text = full_text
                print(f"[SCRAPER] ⚠ No structured data found, using raw text only")
            
            # Clean and chunk
            combined_text = ' '.join(combined_text.split())
            chunks = [combined_text[i:i+1000] for i in range(0, len(combined_text), 1000)]
            chunks = [chunk for chunk in chunks if len(chunk.strip()) > 20]
            
            print(f"[SCRAPER] ✓✓✓ SUCCESS: Created {len(chunks)} chunks")
            print(f"[SCRAPER] First chunk preview: {chunks[0][:150]}...")
            print(f"{'='*80}\n")
            
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