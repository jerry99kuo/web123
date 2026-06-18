from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.models import Article, SiteConfig, get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# --- 文章列表頁面 ---
@router.get("/articles")
async def articles_list(request: Request, session: Session = Depends(get_session)):
    
    # 【資料庫查詢】把 Article 資料表裡面的「所有」文章都抓出來 (all)
    articles = session.exec(select(Article)).all()
    
    # 抓取網站設定 (為了顯示網頁上方的共通標題)
    config = session.exec(select(SiteConfig)).first()
    
    # 包裝給 HTML 使用
    data = {
        "home": {
            "title": config.home_title if config else "",
            "subtitle": config.home_subtitle if config else ""
        },
        "articles": articles
    }
    return templates.TemplateResponse(request = request, name = "articles.html", context = {"request": request, "data": data})

# --- 單篇文章詳情頁面 ---
@router.get("/article/{article_id}")
async def article_detail(request: Request, article_id: int, session: Session = Depends(get_session)):
    
    # 【資料庫查詢：終極魔法】直接用 ID 向資料庫要特定的一篇文章。找不到就會回傳 None
    # 附註：用這種方式抓出來的 article，SQLModel 會自動把底下的 chapters 也一併抓出來！
    article = session.get(Article, article_id)
    
    # 如果資料庫裡沒有這個 ID 的文章，就丟出 404 找不到網頁的錯誤
    if article is None:
        raise HTTPException(status_code=404, detail="找不到該篇文章")
        
    config = session.exec(select(SiteConfig)).first()
    data = {"home": {"title": config.home_title if config else ""}}
    
    return templates.TemplateResponse(request=request, name="article_detail.html", context={"request": request, "article": article, "data": data})