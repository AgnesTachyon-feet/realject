from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from config import get_db
from core.hashing import hash_password, verify_password
from tables.users import Users

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="templates")

@router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register_action(request: Request, username: str = Form(...), email: str = Form(...),
                    password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    if db.query(Users).filter(Users.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "ชื่อผู้ใช้ซ้ำ"})
    user = Users(username=username, email=email, password=hash_password(password), role=role)
    db.add(user); db.commit()
    return RedirectResponse("/login", status_code=303)

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_action(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "รหัสผิด"})
    if user.role == "parent":
        return RedirectResponse(f"/parent/dashboard/{user.id}", status_code=303)
    return RedirectResponse(f"/kid/dashboard/{user.id}", status_code=303)
