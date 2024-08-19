import requests
import random
import urllib3
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode
from requests.adapters import HTTPAdapter

def convert_to_affiliate_link(original_url, channel_id, partners_code):
    parsed_url = urlparse(original_url)
    query_params = parse_qs(parsed_url.query)
    
    product_id = query_params.get('itemId', [''])[0]
    vendor_item_id = query_params.get('vendorItemId', [''])[0]
    
    if not product_id or not vendor_item_id:
        return original_url

    affiliate_params = {
        "lptag": partners_code,
        "subid": channel_id,
        "pageKey": product_id,
        "itemId": product_id,
        "vendorItemId": vendor_item_id,
        "traceid": "V0-153"
    }
    
    return f"https://link.coupang.com/re/AFFSDP?{urlencode(affiliate_params)}"

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def search_coupang(query, num_products=10, sort_by="", channel_id="", partners_code=""):
    base_url = "https://www.coupang.com/np/search"
    params = {
        "q": query,
        "channel": "user",
        "component": "",
        "eventCategory": "",
        "trcid": "",
        "traid": "",
        "sorter": sort_by if sort_by != "coupang_ranking" else "",
        "listSize": max(num_products, 20)  # Ensure we get enough products
    }
    url = f"{base_url}?{urlencode(params)}"
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]

    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        response = requests_retry_session().get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        products = []
        for item in soup.select('li.search-product'):
            product = {
                'name': item.select_one('div.name').text.strip() if item.select_one('div.name') else "N/A",
                'price': item.select_one('strong.price-value').text.strip() if item.select_one('strong.price-value') else "0",
                'rating': item.select_one('em.rating').text.strip() if item.select_one('em.rating') else 'N/A',
                'review_count': item.select_one('span.rating-total-count').text.strip('()') if item.select_one('span.rating-total-count') else '0',
                'url': convert_to_affiliate_link('https://www.coupang.com' + item.select_one('a')['href'], channel_id, partners_code) if item.select_one('a') else "",
                'image_url': item.select_one('img.search-product-wrap-img')['src'] if item.select_one('img.search-product-wrap-img') else '',
            }
            products.append(product)
            
            if len(products) >= num_products:
                break
        
        return products
    except requests.RequestException as e:
        print(f"Error occurred: {e}")
        return []