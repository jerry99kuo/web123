from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Any, Dict, Optional

# 🌟 導入 load_data 函式，假設它位於 app.page_admin 模組中
# ⚠️ 注意：如果你的 load_data 在不同的檔案，請修改此行
try:
    from .page_admin import load_data
except ImportError:
    # 如果找不到，則使用一個簡單的預設資料，但在生產環境中應該修復導入路徑
    def load_data():
        return {
            "home": {"title": "軟體開發者 | 網站工程師"},
            "articles": [
                {
                    "id": 1,
                    "title": "（錯誤：未找到 data.json）",
                    "summary": "請檢查後台 page_admin.py 的 load_data 導入路徑。",
                    "chapters": [],
                },
            ]
        }


# --- 初始化 ---
templates = Jinja2Templates(directory="app/templates")

# 建立 FastAPI 路由實例
router = APIRouter()

# ----------------------------------------------------
# 路由 (Endpoints)
# ----------------------------------------------------

# --- 定義文章列表路由 ---
@router.get("/articles")
async def articles_list(request: Request):
    """
    顯示所有文章的列表頁面 (articles.html)。
    URL: /articles
    """
    # 🌟 從 JSON 檔案載入最新的資料
    data = load_data() 
    
    # 檢查是否成功載入
    if "articles" not in data:
        data["articles"] = []
        
    # 傳遞完整的 data 給模板
    return templates.TemplateResponse(
        "articles.html", 
        {"request": request, "data": data}
    )

# --- 定義單篇文章詳情路由 (支援集數導航) ---
@router.get("/article/{article_id}")
async def article_detail(request: Request, article_id: int):
    """
    顯示單篇文章的詳情頁面 (article_detail.html)。
    它會根據 article_id 找到對應的文章資料。
    URL: /article/1
    """
    # 🌟 從 JSON 檔案載入最新的資料
    data = load_data() 
    
    # 尋找與 article_id 相符的文章
    article: Optional[Dict[str, Any]] = next(
        (a for a in data.get('articles', []) if a.get('id') == article_id), None
    )

    if article is None:
        # 如果找不到文章，導向 404
        # 這裡使用 HTTPException 確保狀態碼正確，並提供一個簡單的錯誤頁面
        raise HTTPException(status_code=404, detail="Article not found")

    # 傳遞單篇文章資料給模板
    return templates.TemplateResponse(
        "article_detail.html", 
        {"request": request, "article": article, "data": data} # 傳遞 data 以便獲取 home 等通用資訊
    )

# ⚠️ 附註：
# 1. 為了讓 article_detail 也能拿到 home.title 等通用資訊，我新增了 "data": data 到 article_detail 的 context 中。
# 2. 我用 load_data() 替換了寫死的 data 字典。
# 3. 如果找不到文章，我使用 HTTPException(404) 來代替重導向到 index.html。