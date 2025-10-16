from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
name = "Jerry"

@router.get("/link", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("link.html", {"request": request, "name" : name})