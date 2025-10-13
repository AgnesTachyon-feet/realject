from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from config import get_db
from fastapi.templating import Jinja2Templates
from tables.users import Users, RoleEnum
from core.auth import hash_password, verify_password

templates = Jinja2Templates(directory="templates")
router = APIRouter(tags=["Auth"])

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}
        )

    if not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}
        )

    if user.role == RoleEnum.kid:
        return RedirectResponse(f"/kid/dashboard/{user.id}", status_code=303)
    elif user.role == RoleEnum.parent:
        return RedirectResponse(f"/parent/dashboard/{user.id}", status_code=303)
    else:
        return RedirectResponse("/login", status_code=303)

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.query(Users).filter(Users.username == username).first()
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "ชื่อผู้ใช้นี้ถูกใช้แล้ว"},
        )

    hashed_pw = hash_password(password)

    new_user = Users(
        username=username,
        password=hashed_pw,
        first_name=first_name,
        role=RoleEnum(role),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse("/login", status_code=303)