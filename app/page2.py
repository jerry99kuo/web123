from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/page2")
def page2(request: Request):
    return templates.TemplateResponse("page2.html", {"request": request})