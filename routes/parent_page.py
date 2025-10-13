from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from config import get_db, templates
from tables.users import Users, RoleEnum
from tables.families import Family, FamilyMember
from tables.rewards import Reward
from utils.family import create_family

router = APIRouter(prefix="/parent", tags=["Parent Pages"])

@router.get("/dashboard/{pid}", response_class=HTMLResponse)
def dashboard_parent(pid: int, request: Request, db: Session = Depends(get_db)):
    parent = db.get(Users, pid)
    if not parent or parent.role != RoleEnum.parent:
        return RedirectResponse("/login", status_code=303)

    fam = db.query(Family).filter(Family.owner_parent_id == pid).first()
    # โชว์เฉพาะ kids ในบ้านเดียวกัน (แนะนำ)
    kids = db.query(Users).join(FamilyMember, FamilyMember.user_id == Users.id).filter(
        FamilyMember.family_id.in_(
            db.query(FamilyMember.family_id).filter(FamilyMember.user_id == pid)
        ),
        Users.role == RoleEnum.kid
    ).all()

    rewards = db.query(Reward).filter(Reward.parent_id == pid).all()

    return templates.TemplateResponse("dashboard_parent.html", {
        "request": request,
        "parent": parent,
        "pid": pid,
        "family_code": fam.code if fam else None,
        "kids": kids,
        "rewards": rewards
    })

@router.post("/{pid}/family/create")
def create_family_route(pid: int, family_name: str = Form(...), db: Session = Depends(get_db)):
    parent = db.get(Users, pid)
    if not parent or parent.role != RoleEnum.parent:
        return RedirectResponse("/login", status_code=303)
    name = family_name.strip()
    if not (1 <= len(name) <= 80):
        return RedirectResponse(f"/parent/dashboard/{pid}?err=bad_name", status_code=303)
    exists = db.query(Family).filter(Family.owner_parent_id == pid).first()
    if exists:
        return RedirectResponse(f"/parent/dashboard/{pid}?ok=already_have&code={exists.code}", status_code=303)
    fam = create_family(db, parent_id=pid, family_name=name)
    return RedirectResponse(f"/parent/dashboard/{pid}?ok=created&code={fam.code}", status_code=303)