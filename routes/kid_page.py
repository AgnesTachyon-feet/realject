from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from config import get_db, templates
from tables.users import Users, RoleEnum
from tables.families import FamilyMember, Family
from utils.family import join_family

router = APIRouter(prefix="/kid", tags=["Kid Pages"])

@router.get("/dashboard/{kid_id}", response_class=HTMLResponse)
def dashboard_kid(request: Request, kid_id: int, db: Session = Depends(get_db)):
    kid = db.get(Users, kid_id)
    if not kid or getattr(kid.role, "value", str(kid.role)) != "kid":
        return RedirectResponse("/login", status_code=303)

    member = db.query(FamilyMember).filter(FamilyMember.user_id == kid_id).first()
    family = db.get(Family, member.family_id) if member else None

    return templates.TemplateResponse("dashboard_kid.html", {
        "request": request,
        "kid": kid,
        "in_family": bool(member),
        "family_name": family.name if family else None
    })

@router.post("/join")
def kid_join(kid_id: int = Form(...), code: str = Form(...), db: Session = Depends(get_db)):
    try:
        join_family(db, kid_id=kid_id, code=code)
        return RedirectResponse(f"/kid/dashboard/{kid_id}?ok=joined", status_code=303)
    except ValueError:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=invalid_code", status_code=303)