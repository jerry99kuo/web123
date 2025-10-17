from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
DATA_FILE = "app/data.json"

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = load_data()
    return templates.TemplateResponse("home.html", {"request": request, "name": "Jerry Kuo", "data": data})
