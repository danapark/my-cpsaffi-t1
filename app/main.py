import os
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .web_scraper import search_coupang
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

# 프로젝트 루트 디렉토리 경로 계산
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(ROOT_DIR, "static")

logger.debug(f"Project root directory: {ROOT_DIR}")
logger.debug(f"Static directory: {STATIC_DIR}")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open(os.path.join(STATIC_DIR, "index.html"), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

# 나머지 코드는 그대로 유지

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("../static/index.html", "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

@app.post("/search")
async def search(
    query: str = Form(...),
    sort_by: str = Form("coupang_ranking"),
    product_count: int = Form(10),
    channel_id: str = Form(...),
    partners_code: str = Form(...)
):
    logger.debug(f"Received request: query={query}, sort_by={sort_by}, product_count={product_count}, channel_id={channel_id}, partners_code={partners_code}")
    if not channel_id or not partners_code:
        raise HTTPException(status_code=400, detail="채널 ID와 파트너스 코드를 입력해주세요.")
    
    results = search_coupang(query, num_products=product_count, sort_by=sort_by,
                             channel_id=channel_id, partners_code=partners_code)
    
    if not results:
        return JSONResponse(content={"error": "검색 결과가 없습니다."})
    
    processed_data = process_data(results)
    if sort_by != "coupang_ranking":
        processed_data = sort_products(processed_data, sort_by)
    analysis = analyze_data(processed_data)
    
    return JSONResponse(content={"results": processed_data, "analysis": analysis})