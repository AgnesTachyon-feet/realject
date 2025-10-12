from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from config import get_db, templates
from tables.users import Users
from tables.families import Family, FamilyMember

router = APIRouter(tags=["Kid Pages"], prefix="/kid")

def _kid_in_family(db: Session, kid_id: int):
    link = db.query(FamilyMember).filter(FamilyMember.user_id == kid_id, FamilyMember.role == "kid").first()
    return bool(link)

@router.get("/dashboard/{kid_id}")
def dashboard_kid(request: Request, kid_id: int, db: Session = Depends(get_db)):
    kid = db.query(Users).get(kid_id)
    if not kid or kid.role != "kid":
        return RedirectResponse("/login", status_code=303)

    in_family = _kid_in_family(db, kid_id)

    return templates.TemplateResponse("dashboard_kid.html", {
        "request": request,
        "kid": kid,
        "not_in_family": not in_family
    })

@router.post("/join")
def kid_join_family(kid_id: int = Form(...), code: str = Form(...), db: Session = Depends(get_db)):
    kid = db.query(Users).get(kid_id)
    if not kid or kid.role != "kid":
        return RedirectResponse("/login", status_code=303)

    fam = db.query(Family).filter(Family.code == code.strip()).first()
    if not fam:
        return RedirectResponse(f"/kid/dashboard/{kid_id}", status_code=303)

    exists = db.query(FamilyMember).filter(
        FamilyMember.family_id == fam.id,
        FamilyMember.user_id == kid_id
    ).first()
    if not exists:
        db.add(FamilyMember(family_id=fam.id, user_id=kid_id, role="kid"))
        db.commit()

    return RedirectResponse(f"/kid/dashboard/{kid_id}", status_code=303)