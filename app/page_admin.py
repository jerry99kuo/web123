from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
import json
import os

router = APIRouter()

DATA_FILE = "app/data.json"
ADMIN_PASSWORD = "1234"  # 可以改更安全

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 登入頁
@router.get("/admin")
def admin(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.post("/admin")
def admin_login(password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        return RedirectResponse("/admin/edit", status_code=302)
    else:
        return RedirectResponse("/admin", status_code=302)

# 編輯頁
@router.get("/admin/edit")
def admin_edit(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    data = load_data()
    return templates.TemplateResponse("admin_edit.html", {"request": request, "data": data})

@router.post("/admin/edit")
def admin_update(
    home_title: str = Form(...),
    home_subtitle: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    link1: str = Form(...),
    link2: str = Form(...),
):
    data = load_data()
    data["home"]["title"] = home_title
    data["home"]["subtitle"] = home_subtitle
    data["contact"]["email"] = email
    data["contact"]["phone"] = phone
    data["links"]["link1"] = link1
    data["links"]["link2"] = link2
    save_data(data)
    return RedirectResponse("/admin/edit", status_code=302)