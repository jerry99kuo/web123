from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.models import Link, get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/link", response_class=HTMLResponse)
async def contact(request: Request, session: Session = Depends(get_session)):
    
    # 【資料庫查詢】去 Link 資料表把所有的常用連結撈出來
    links_from_db = session.exec(select(Link)).all()
    
    # 包裝在字典裡，對應舊版 JSON 的 {"links": [...]} 結構
    data = {"links": links_from_db}
    
    return templates.TemplateResponse("link.html", {"request": request, "name": "Jerry Kuo", "data": data})