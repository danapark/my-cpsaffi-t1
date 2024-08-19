from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from web_scraper import search_coupang
from data_processor import process_data, analyze_data, sort_products

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

@app.post("/search")
async def search(query: str = Form(...), sort_by: str = Form("coupang_ranking"), product_count: int = Form(10)):
    results = search_coupang(query, num_products=product_count, sort_by=sort_by)
    
    if not results:
        return JSONResponse(content={"error": "검색 결과가 없습니다."})
    
    processed_data = process_data(results)
    if sort_by != "coupang_ranking":
        processed_data = sort_products(processed_data, sort_by)
    processed_data = processed_data[:product_count]  # Ensure we only return the requested number of products
    analysis = analyze_data(processed_data)
    
    return JSONResponse(content={"results": processed_data, "analysis": analysis})