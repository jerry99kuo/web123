from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.models import Portfolio, get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/portfolio", response_class=HTMLResponse)
async def portfolio(request: Request, session: Session = Depends(get_session)):
    
    # 【資料庫查詢】撈出所有作品，並透過 order_by 讓「最新建立的」排在最上面
    statement = select(Portfolio).order_by(Portfolio.id.desc())
    projects = session.exec(statement).all()
    
    # 把 projects 傳給 portfolio.html，讓它可以用 {% for project in projects %} 跑迴圈印出畫面
    return templates.TemplateResponse(
        request=request, 
        name="portfolio.html", 
        context={"request": request, "projects": projects, "name": "Jerry Kuo"}
    )