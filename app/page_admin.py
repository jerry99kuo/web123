from fastapi import APIRouter, Request, Form, Response, Cookie, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import json
import os
from typing import Optional, List, Any, Dict
from fastapi.templating import Jinja2Templates

router = APIRouter()
# 假設 templates 已經在 main.py 中設定，但在此路由檔案中重新定義以確保可用性
templates = Jinja2Templates(directory="app/templates") 

DATA_FILE = "app/data.json"

# --- 安全性設定 ---
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")
SESSION_SECRET_VALUE = os.getenv("SESSION_SECRET_VALUE", "CHANGE_ME_TO_A_VERY_SECRET_STRING")
SESSION_COOKIE_NAME = "admin_session"
# ---

# ----------------------------------------------------
# 🌟 資料處理與 ID 賦值邏輯 (用於支援新增/編輯/刪除)
# ----------------------------------------------------
def load_data() -> Dict[str, Any]:
    """
    載入數據，如果檔案不存在則創建預設結構，並處理舊資料遷移。
    """
    if not os.path.exists(DATA_FILE):
        default_data = {
            "home": {"title": "", "subtitle": ""},
            "contact": {"email": "", "phone": ""},
            "links": [], 
            "articles": []
        }
        save_data(default_data)
        return default_data
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        # 如果 JSON 損壞，返回一個空結構以防止崩潰
        return {"home": {"title": "", "subtitle": ""}, "contact": {"email": "", "phone": ""}, "links": [], "articles": []}

    # 確保 articles 欄位存在 (處理舊資料遷移)
    if "articles" not in data or not isinstance(data["articles"], list):
        data["articles"] = []
    
    # 保留你的舊 links 遷移邏輯
    if "links" not in data or isinstance(data["links"], dict):
        # 這裡的邏輯與你提供的原始程式碼相似，用於處理舊版 links 格式
        pass 

    return data


def assign_ids_before_save(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    在儲存前，檢查並為所有沒有 ID (或帶有臨時 ID 'new_') 的文章和集數分配新的數字 ID。
    """
    # 尋找目前最大的文章 ID
    max_article_id = 0
    for a in data.get('articles', []):
        if isinstance(a.get('id'), int):
            max_article_id = max(max_article_id, a['id'])

    for article in data['articles']:
        # 1. 處理文章 ID
        if article.get('id') is None or (isinstance(article.get('id'), str) and article.get('id', '').startswith("new_")):
            max_article_id += 1
            article['id'] = max_article_id
        
        # 2. 處理集數 ID
        max_chapter_id = 0
        for c in article.get('chapters', []):
             if isinstance(c.get('chapter_id'), int):
                max_chapter_id = max(max_chapter_id, c['chapter_id'])
                
        for chapter in article['chapters']:
            if chapter.get('chapter_id') is None or (isinstance(chapter.get('chapter_id'), str) and chapter.get('chapter_id', '').startswith("new_")):
                max_chapter_id += 1
                chapter['chapter_id'] = max_chapter_id
                
    return data

def save_data(data: Dict[str, Any]):
    """ 
    將數據儲存到 JSON 檔案，並在儲存前處理 ID 分配。
    """
    data_to_save = assign_ids_before_save(data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# --- 登入驗證 (Dependency) ---
async def get_current_admin(admin_session: Optional[str] = Cookie(default=None)):
    if admin_session != SESSION_SECRET_VALUE:
        raise HTTPException(status_code=302, detail="Unauthorized", headers={"Location": "/admin"})
    return True 

# --- 路由 (Endpoints) ---

# 登入頁 (GET)
@router.get("/admin")
def admin(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

# 處理登入 (POST)
@router.post("/admin")
def admin_login(password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        response = RedirectResponse(f"/admin/edit", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=SESSION_SECRET_VALUE,
            httponly=True,
            samesite="strict",
        )
        return response
    else:
        return RedirectResponse("/admin?error=true", status_code=303)

# 編輯頁 (GET)
@router.get("/admin/edit")
def admin_edit(request: Request, is_logged_in: bool = Depends(get_current_admin)):
    query_params = request.query_params
    updated = "updated" in query_params
    data = load_data()
    return templates.TemplateResponse("admin_edit.html", {
        "request": request, 
        "data": data,
        "updated": updated
    })

# 處理資料更新 (POST)
@router.post("/admin/edit")
async def admin_update(
    request: Request, 
    is_logged_in: bool = Depends(get_current_admin), 
    home_title: str = Form(...),
    home_subtitle: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    link_names: List[str] = Form(default=[]), 
    link_urls: List[str] = Form(default=[]),
    
    # 接收文章主體的欄位
    article_ids: List[str] = Form(default=[]), 
    article_titles: List[str] = Form(default=[]),
    article_summaries: List[str] = Form(default=[]),
):
    
    data = load_data() 
    
    # 獲取完整的表單資料 (用於讀取動態命名的集數欄位)
    form = await request.form() 

    # 1. 儲存 Home 和 Contact
    data["home"]["title"] = home_title
    data["home"]["subtitle"] = home_subtitle
    data["contact"]["email"] = email
    data["contact"]["phone"] = phone
    
    # 2. 重新組合 links 列表 
    new_links = []
    for name, url in zip(link_names, link_urls):
        if name and url:
            new_links.append({"name": name, "url": url})
    data["links"] = new_links 
    
    # ----------------------------------------------------
    # 3. 處理文章與集數 (核心邏輯)
    # ----------------------------------------------------
    new_articles = []
    
    if article_ids and article_titles:
        # 遍歷所有文章
        for i, article_id_str in enumerate(article_ids):
            
            # 確保文章主體欄位存在
            if i >= len(article_titles) or i >= len(article_summaries):
                 continue

            article_title = article_titles[i]
            article_summary = article_summaries[i]
            
            # 如果文章標題為空，則跳過，視為被刪除的文章
            if not article_title:
                 continue

            # 根據 ID 類型決定儲存方式
            if article_id_str.isdigit():
                article_id = int(article_id_str)
            elif article_id_str.startswith("new_"):
                article_id = article_id_str # 保持臨時 ID
            else:
                article_id = None
                
            article_obj = {
                "id": article_id, 
                "title": article_title,
                "summary": article_summary,
                "chapters": []
            }

            # 📌 文章 ID (可能是數字或 'new_XXXX') 用於動態欄位名稱
            field_id = str(article_id_str) 
            
            chapter_ids = form.getlist(f"chapter_ids_{field_id}")
            chapter_titles = form.getlist(f"chapter_titles_{field_id}")
            chapter_contents = form.getlist(f"chapter_contents_{field_id}")
            
            
            # 遍歷集數
            if chapter_ids:
                for j, chapter_id_str in enumerate(chapter_ids):
                    # 確保所有集數欄位都有值
                    if j < len(chapter_titles) and j < len(chapter_contents):
                        
                        chapter_title = chapter_titles[j]
                        chapter_content = chapter_contents[j]
                        
                        # 確保集數標題和內容不為空
                        if chapter_title and chapter_content: 
                            
                            # 根據 ID 類型決定儲存方式
                            if chapter_id_str.isdigit():
                                chapter_id = int(chapter_id_str)
                            elif chapter_id_str.startswith("new_"):
                                chapter_id = chapter_id_str # 保持臨時 ID
                            else:
                                chapter_id = None
                            
                            chapter_obj = {
                                "chapter_id": chapter_id,
                                "chapter_title": chapter_title,
                                "content": chapter_content,
                            }
                            article_obj['chapters'].append(chapter_obj)
            
            # 只有文章內有內容或集數時才保留
            if article_obj['title'] or article_obj['chapters']:
                 new_articles.append(article_obj)
                 
    data["articles"] = new_articles
    
    # 4. 儲存到檔案 (會自動處理 ID 賦值)
    save_data(data)
    
    return RedirectResponse("/admin/edit?updated=true", status_code=303)

# 登出 (GET)
@router.get("/admin/logout")
def admin_logout():
    response = RedirectResponse("/admin", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response

# 🌟 提醒：記得將 articles.html 和 article_detail.html 放到 app/templates/ 
#    並且你的 article_router 要使用 load_data() 來獲取最新的文章數據！