from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# 🔽 新增：引入設定生命週期需要的工具，以及 SQLModel
from contextlib import asynccontextmanager
from sqlmodel import SQLModel

# 🔽 新增：從你的 models 引入資料庫引擎
from app.models import engine

from app.page_home import router as home_router
from app.page_portfolio import router as portfolio_router
from app.page_contact import router as contact_router
from app.link import router as link_router
from app.page_admin import router as admin_router
from app.page_article import router as article_router
from app.page_chess import router as chess_router
from app.api_upload import router as upload_router

# ==========================================
# 設定 FastAPI 啟動與關閉時的動作 (Lifespan)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 正在初始化資料庫...")
    # 這行會去掃描 app.models 裡面的所有資料表，如果不存在就會自動建立！
    SQLModel.metadata.create_all(engine)
    print("✅ 資料庫初始化完成！")
    yield
    print("🛑 伺服器正在關閉...")

# 建立 FastAPI 實例，並綁定 lifespan
app = FastAPI(lifespan=lifespan)

# 靜態檔 (不變)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 註冊路由 (不變)
app.include_router(home_router)
app.include_router(portfolio_router)
app.include_router(contact_router)
app.include_router(link_router)
app.include_router(admin_router)
app.include_router(article_router)
app.include_router(chess_router)
app.include_router(upload_router)
