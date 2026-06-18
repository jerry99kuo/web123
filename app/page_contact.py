from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.models import SiteConfig, get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, session: Session = Depends(get_session)):
    
    # 【資料庫查詢】取得聯絡資訊
    config = session.exec(select(SiteConfig)).first()
    
    # 轉換成原本 JSON 的結構，這樣 HTML 裡的 {{ data.contact.email }} 才抓得到東西
    data = {
        "contact": {
            "email": config.email if config else "目前無 Email",
            "phone": config.phone_number if config else "目前無電話"
        }
    }
    return templates.TemplateResponse(request=request, name="contact.html", context={"request": request, "name": "Jerry Kuo", "data": data})