from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
from .data_processor import process_data, analyze_data, sort_products
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

async def fetch_coupang(url: str, headers: dict):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=120.0)
    return response.text

@app.post("/search")
async def search(
    query: str = Form(...),
    sort_by: str = Form("coupang_ranking"),
    product_count: int = Form(10),
    channel_id: str = Form(...),
    partners_code: str = Form(...)
):
    if not channel_id or not partners_code:
        return JSONResponse(content={"error": "채널 ID와 파트너스 코드를 입력해주세요."}, status_code=400)
    
    url = f"https://www.coupang.com/np/search?q={query}&channel=user&component=&eventCategory=&trcid=&traid=&sorter={sort_by}&listSize={max(product_count, 20)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=120.0)
        content = response.text
        logger.debug(f"Coupang response status: {response.status_code}")
        logger.debug(f"Coupang response content (first 500 chars): {content[:500]}")
        
        soup = BeautifulSoup(content, 'html.parser')
        
        products = []
        for item in soup.select('li.search-product')[:product_count]:
            product = {
                'name': item.select_one('div.name').text.strip() if item.select_one('div.name') else "N/A",
                'price': item.select_one('strong.price-value').text.strip() if item.select_one('strong.price-value') else "0",
                'rating': item.select_one('em.rating').text.strip() if item.select_one('em.rating') else 'N/A',
                'review_count': item.select_one('span.rating-total-count').text.strip('()') if item.select_one('span.rating-total-count') else '0',
                'url': f"https://link.coupang.com/re/AFFSDP?lptag={partners_code}&subid={channel_id}&pageKey={item.select_one('a')['data-item-id']}&traceid=V0-153" if item.select_one('a') else "",
                'image_url': item.select_one('img.search-product-wrap-img')['src'] if item.select_one('img.search-product-wrap-img') else '',
            }
            products.append(product)
        
        if not products:
            return JSONResponse(content={"error": "검색 결과가 없습니다."})
        
        processed_data = process_data(products)
        if sort_by != "coupang_ranking":
            processed_data = sort_products(processed_data, sort_by)
        analysis = analyze_data(processed_data)
        
        return JSONResponse(content={"results": processed_data, "analysis": analysis})
    except Exception as e:
        logger.exception("Error occurred during search")
        return JSONResponse(content={"error": f"검색 중 오류가 발생했습니다: {str(e)}"}, status_code=500)