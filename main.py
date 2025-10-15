from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.page_home import router as home_router
from app.page_portfolio import router as portfolio_router
from app.page_contact import router as contact_router

app = FastAPI()

# 靜態檔
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板資料夾
templates = Jinja2Templates(directory="app/templates")

# 註冊路由
app.include_router(home_router)
app.include_router(portfolio_router)
app.include_router(contact_router)