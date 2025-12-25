from __future__ import annotations
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship



class SiteConfig(SQLModel, table = True):
    id: int|None = Field(default=None, primary_key=True)
    home_title : str
    home_subtitle : str
    email : str
    phone_number : str
    
class Link(SQLModel, table=True):
    id : int|None = Field(default=None, primary_key=True)
    name : str
    url : str

class Article(SQLModel, table = True):
    id : int|None = Field(default=None, primary_key=True)
    title : str
    summary : str | None = None
    
    chapters: List[Chapter] = Relationship(back_populates="article", cascade_delete=True)

class Chapter(SQLModel, table = True):
    id : int|None = Field(default=None, primary_key=True)
    title : str
    content : str
    
    article_id: Optional[int] = Field(default=None, foreign_key="article.id")
    article: Optional["Article"] = Relationship(back_populates="chapters")
    