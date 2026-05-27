from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.models import Portfolio, get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/portfolio", response_class=HTMLResponse)
async def portfolio(request: Request, session: Session = Depends(get_session)):
    
    # 【資料庫查詢】去 Portfolio 資料表把所有的作品清單都撈出來
    projects = session.exec(select(Portfolio)).all()
    
    # 把 projects 傳給 portfolio.html，讓它可以用 {% for project in projects %} 跑迴圈印出畫面
    return templates.TemplateResponse("portfolio.html", {"request": request, "projects": projects, "name": "Jerry Kuo"})