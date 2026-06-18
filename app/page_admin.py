from fastapi import APIRouter, Request, Form, Response, Cookie, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
import os

# 🌟 確認這裡有匯入 Portfolio
from sqlmodel import Session, select, delete
from app.models import SiteConfig, Link, Article, Chapter, Portfolio, engine, get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates") 

# --- 安全性設定 ---
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "0968780188")
SESSION_SECRET_VALUE = os.getenv("SESSION_SECRET_VALUE", "CHANGE_ME_TO_A_VERY_SECRET_STRING")
SESSION_COOKIE_NAME = "admin_session"
# ---

# ==========================================
# 取得資料庫連線 (Dependency)
# ==========================================
def get_session():
    with Session(engine) as session:
        yield session

# --- 登入驗證 (Dependency) ---
async def get_current_admin(admin_session: Optional[str] = Cookie(default=None)):
    if admin_session != SESSION_SECRET_VALUE:
        raise HTTPException(status_code=302, detail="Unauthorized", headers={"Location": "/admin"})
    return True 

# ==========================================
# 路由 (Endpoints)
# ==========================================

# 1. 登入頁 (GET)
@router.get("/admin")
def admin(request: Request):
    return templates.TemplateResponse(request = request, name = "admin_login.html", context = {"request": request})

# 2. 處理登入 (POST)
@router.post("/admin")
def admin_login(password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        response = RedirectResponse("/admin/edit", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=SESSION_SECRET_VALUE,
            httponly=True,
            samesite="strict",
        )
        return response
    else:
        return RedirectResponse("/admin?error=true", status_code=303)

# 3. 編輯頁 (GET)
@router.get("/admin/edit")
def admin_edit(request: Request, session: Session = Depends(get_session), is_logged_in: bool = Depends(get_current_admin)):
    query_params = request.query_params
    updated = "updated" in query_params
    
    # 從資料庫撈取所有資料
    config = session.exec(select(SiteConfig)).first()
    links = session.exec(select(Link)).all()
    articles = session.exec(select(Article)).all()
    
    # 🌟 新增：從資料庫撈取作品集
    portfolios = session.exec(select(Portfolio)).all()

    if not config:
        config = SiteConfig(home_title="", home_subtitle="", email="", phone_number="")

    data = {
        "home": {"title": config.home_title, "subtitle": config.home_subtitle},
        "contact": {"email": config.email, "phone": config.phone_number},
        "links": [{"name": link.name, "url": link.url} for link in links],
        "articles": [],
        # 🌟 新增：打包 Portfolio 給前端
        "portfolios": [{"id": p.id, "name": p.name, "desc": p.desc, "link": p.link} for p in portfolios]
    }

    # 組合文章與集數
    for a in articles:
        article_dict = {
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "chapters": [
                {"chapter_id": c.id, "chapter_title": c.title, "content": c.content} 
                for c in a.chapters
            ]
        }
        data["articles"].append(article_dict)

    return templates.TemplateResponse(request=request, name = "admin_edit.html", context={
        "request": request, 
        "data": data,
        "updated": updated
    })

# 4. 處理資料更新 (POST)
@router.post("/admin/edit")
async def admin_update(
    request: Request, 
    session: Session = Depends(get_session),
    is_logged_in: bool = Depends(get_current_admin), 
    home_title: str = Form(...),
    home_subtitle: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    link_names: List[str] = Form(default=[]), 
    link_urls: List[str] = Form(default=[]),
    article_ids: List[str] = Form(default=[]), 
    article_titles: List[str] = Form(default=[]),
    article_summaries: List[str] = Form(default=[]),
    # 🌟 新增：接收 Portfolio 表單資料
    portfolio_ids: List[str] = Form(default=[]),
    portfolio_names: List[str] = Form(default=[]),
    portfolio_descs: List[str] = Form(default=[]),
    portfolio_links: List[str] = Form(default=[])
):
    form = await request.form() 

    # --- 1. 更新首頁與聯絡資訊 ---
    config = session.exec(select(SiteConfig)).first()
    if not config:
        config = SiteConfig(home_title=home_title, home_subtitle=home_subtitle, email=email, phone_number=phone)
        session.add(config)
    else:
        config.home_title = home_title
        config.home_subtitle = home_subtitle
        config.email = email
        config.phone_number = phone

    # --- 2. 更新常用連結 ---
    session.exec(delete(Link))
    for name, url in zip(link_names, link_urls):
        if name and url:
            session.add(Link(name=name, url=url))

    # --- 3. 更新作品集 (Portfolio) 🌟 ---
    existing_portfolios = session.exec(select(Portfolio)).all()
    existing_portfolio_map = {str(p.id): p for p in existing_portfolios}
    submitted_portfolio_ids = set()

    if portfolio_ids and portfolio_names:
        for i, p_id_str in enumerate(portfolio_ids):
            if i >= len(portfolio_names): continue
            
            p_name = portfolio_names[i]
            p_desc = portfolio_descs[i] if i < len(portfolio_descs) else ""
            p_link = portfolio_links[i] if i < len(portfolio_links) else ""
            
            if not p_name: continue # 名稱空白視為無效

            if p_id_str.isdigit() and p_id_str in existing_portfolio_map:
                # 更新舊作品
                port = existing_portfolio_map[p_id_str]
                port.name = p_name
                port.desc = p_desc
                port.link = p_link
                submitted_portfolio_ids.add(p_id_str)
            else:
                # 新增新作品
                new_port = Portfolio(name=p_name, desc=p_desc, link=p_link)
                session.add(new_port)

    # 刪除被使用者在前端按移除的作品
    for p_id_str, existing_p in existing_portfolio_map.items():
        if p_id_str not in submitted_portfolio_ids:
            session.delete(existing_p)

    # --- 4. 更新文章與集數 ---
    existing_articles = session.exec(select(Article)).all()
    existing_article_map = {str(a.id): a for a in existing_articles}
    submitted_article_ids = set() 

    if article_ids and article_titles:
        for i, article_id_str in enumerate(article_ids):
            if i >= len(article_titles): continue
            
            title = article_titles[i]
            summary = article_summaries[i] if i < len(article_summaries) else ""
            if not title: continue 

            if article_id_str.isdigit() and article_id_str in existing_article_map:
                article = existing_article_map[article_id_str]
                article.title = title
                article.summary = summary
                submitted_article_ids.add(article_id_str)
            else:
                article = Article(title=title, summary=summary)
                session.add(article)

            field_id = str(article_id_str) 
            chapter_ids = form.getlist(f"chapter_ids_{field_id}")
            chapter_titles = form.getlist(f"chapter_titles_{field_id}")
            chapter_contents = form.getlist(f"chapter_contents_{field_id}")

            existing_chapter_map = {str(c.id): c for c in article.chapters}
            submitted_chapter_ids = set()

            for j, chapter_id_str in enumerate(chapter_ids):
                if j >= len(chapter_titles) or j >= len(chapter_contents): continue
                
                c_title = chapter_titles[j]
                c_content = chapter_contents[j]
                if not c_title or not c_content: continue

                if chapter_id_str.isdigit() and chapter_id_str in existing_chapter_map:
                    chapter = existing_chapter_map[chapter_id_str]
                    chapter.title = c_title
                    chapter.content = c_content
                    submitted_chapter_ids.add(chapter_id_str)
                else:
                    new_chapter = Chapter(title=c_title, content=c_content)
                    article.chapters.append(new_chapter)

            for c_id_str, existing_c in existing_chapter_map.items():
                if c_id_str not in submitted_chapter_ids:
                    session.delete(existing_c)

    for a_id_str, existing_a in existing_article_map.items():
        if a_id_str not in submitted_article_ids:
            session.delete(existing_a)

    # --- 5. 統一儲存所有變更 ---
    session.commit()
    
    return RedirectResponse("/admin/edit?updated=true", status_code=303)

# 5. 登出 (GET)
@router.get("/admin/logout")
def admin_logout():
    response = RedirectResponse("/admin", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response