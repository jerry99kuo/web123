from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session

# ==========================================
# 1. 資料庫連線引擎
# ==========================================
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# 建立資料庫引擎
engine = create_engine(sqlite_url, echo=True)

# 共用的 get_session 函式
def get_session():
    with Session(engine) as session:
        yield session

# ==========================================
# 2. 資料庫藍圖 (Models)
# ==========================================
class SiteConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    home_title: str
    home_subtitle: str
    email: str
    phone_number: str
    
class Link(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    url: str

class Article(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    summary: str | None = None
    
    # 🌟 修復核心：將 Chapter 加上引號變成 "Chapter"
    chapters: List["Chapter"] = Relationship(back_populates="article", cascade_delete=True)

class Chapter(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str
    article_id: Optional[int] = Field(default=None, foreign_key="article.id")
    # 這裡的 "Article" 原本就有引號，所以很安全
    article: Optional["Article"] = Relationship(back_populates="chapters")

class Portfolio(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    desc: str
    link: str
    
class Puzzle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    board_str: str 
    solution: str   
    
