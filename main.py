from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from app import page1, page2

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 導入多頁面路由
app.include_router(page1.router)
app.include_router(page2.router)

# 首頁
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})