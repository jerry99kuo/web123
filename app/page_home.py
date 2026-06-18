from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

# 🌟 1. 多引入 Portfolio 模型
from app.models import SiteConfig, Portfolio, get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    
    # 撈取網站設定
    config = session.exec(select(SiteConfig)).first()
    
    # 🌟 2. 撈取最新的 3 筆里程碑/成就紀錄
    statement = select(Portfolio).order_by(Portfolio.id.desc()).limit(3)
    recent_portfolios = session.exec(statement).all()
    
    # 🌟 3. 將 portfolios 加進 data 字典中
    data = {
        "home": {
            "title": config.home_title if config else "歡迎來到我的網站",
            "subtitle": config.home_subtitle if config else "網站建置中..."
        },
        "portfolios": recent_portfolios
    }
    
    return templates.TemplateResponse(
        request=request, 
        name="home.html", 
        context={"request": request, "name": "Jerry Kuo", "data": data}
    )