from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
name = "Jerry"
DATA_FILE = "app/data.json"

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/link", response_class=HTMLResponse)
async def contact(request: Request):
    data = load_data()
    return templates.TemplateResponse("link.html", {"request": request, "name" : name, "data":data})