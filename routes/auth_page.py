from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session
from config import get_db, templates
from tables.users import Users
from core.auth import hash_password, verify_password

router = APIRouter(tags=["Auth Pages"])

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}
        )
    if user.role == "parent":
        return templates.TemplateResponse("dashboard_parent.html", {"request": request, "parent": user})
    else:
        return templates.TemplateResponse("dashboard_kid.html", {"request": request, "kid": user})

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(Users).filter(Users.username == username).first():
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "มีชื่อผู้ใช้นี้แล้ว"}
        )
    user = Users(
        username=username,
        password=hash_password(password),
        first_name=first_name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if role == "parent":
        return templates.TemplateResponse("dashboard_parent.html", {"request": request, "parent": user})
    else:
        return templates.TemplateResponse("dashboard_kid.html", {"request": request, "kid": user})