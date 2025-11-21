from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

@router.get("/chess", response_class=HTMLResponse)
async def chess_page(request: Request):
    return templates.TemplateResponse("chess.html", {"request": request})