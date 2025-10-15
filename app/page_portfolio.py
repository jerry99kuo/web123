from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/portfolio", response_class=HTMLResponse)
async def portfolio(request: Request):
    projects = [
        {"name": "專案1", "desc": "專案描述", "link": "#"},
        {"name": "專案2", "desc": "專案描述", "link": "#"},
    ]
    return templates.TemplateResponse("portfolio.html", {"request": request, "projects": projects, "name" : "Jerry Kuo"})
