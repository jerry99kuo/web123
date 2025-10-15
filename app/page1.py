from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/page1")
def page1(request: Request):
    return templates.TemplateResponse("page1.html", {"request": request})