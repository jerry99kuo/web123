from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

# 引入資料庫連線工具 (get_session) 與首頁的資料表模型 (SiteConfig)
from app.models import SiteConfig, get_session

# 建立這個頁面專屬的路由器
router = APIRouter()
# 設定 Jinja2 模板引擎要去哪裡找 HTML 檔案
templates = Jinja2Templates(directory="app/templates")

# 定義路由：當使用者用 GET 方法訪問首頁 ("/") 時觸發
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    
    # 【資料庫查詢】向資料庫發送請求：給我 SiteConfig 資料表裡的第一筆資料 (first)
    config = session.exec(select(SiteConfig)).first()
    
    # 把資料包裝成原本 data.json 的格式，這樣你的 home.html 就完全不用改程式碼！
    data = {
        "home": {
            # 如果 config 有東西就顯示標題，如果沒有(剛建好資料庫)就顯示預設文字防呆
            "title": config.home_title if config else "歡迎來到我的網站",
            "subtitle": config.home_subtitle if config else "網站建置中..."
        }
    }
    
    # 把 request、你的名字、以及打包好的 data 傳給 home.html 去渲染畫面
    return templates.TemplateResponse(request=request, name="home.html", context={"request": request, "name": "Jerry Kuo", "data": data})