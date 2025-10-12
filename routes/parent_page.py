from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from config import get_db, templates
from tables.users import Users
from tables.families import Family, FamilyMember
import secrets

router = APIRouter(tags=["Parent Pages"], prefix="/parent")

def _find_family_by_parent(db: Session, pid: int):
    fam = db.query(Family).filter(Family.owner_parent_id == pid).first()
    if fam:
        return fam
    link = db.query(FamilyMember).filter(FamilyMember.user_id == pid, FamilyMember.role == "parent").first()
    if link:
        return db.query(Family).get(link.family_id)
    return None

def _gen_code():
    return "FAM-" + secrets.token_hex(3).upper()

@router.get("/dashboard/{pid}")
def dashboard_parent(request: Request, pid: int, db: Session = Depends(get_db)):
    parent = db.query(Users).get(pid)
    if not parent or parent.role != "parent":
        return RedirectResponse("/login", status_code=303)

    fam = _find_family_by_parent(db, pid)
    family_code = fam.code if fam else None

    return templates.TemplateResponse("dashboard_parent.html", {
        "request": request,
        "parent": parent,
        "family_code": family_code,
        "pid": pid
    })

@router.post("/family/create")
def create_family(pid: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    parent = db.query(Users).get(pid)
    if not parent or parent.role != "parent":
        return RedirectResponse("/login", status_code=303)

    fam_exists = _find_family_by_parent(db, pid)
    if fam_exists:
        return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)

    code = _gen_code()
    fam = Family(name=name, code=code, owner_parent_id=pid)
    db.add(fam); db.commit(); db.refresh(fam)

    db.add(FamilyMember(family_id=fam.id, user_id=pid, role="parent"))
    db.commit()
    return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)
