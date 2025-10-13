from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse,HTMLResponse
from sqlalchemy.orm import Session
from config import get_db,templates
from tables.users import Users, RoleEnum
from utils.family import create_family
from tables.families import Family

router = APIRouter(prefix="/parent", tags=["Parent Pages"])

@router.get("/dashboard/{pid}")
def dashboard_parent(pid: int, request: Request, db: Session = Depends(get_db)):

    parent = db.get(Users, pid)
    if not parent:
        return RedirectResponse("/login", status_code=303)

    fam = db.query(Family).filter(Family.owner_parent_id == pid).first()
    family_code = fam.code if fam else None

    return templates.TemplateResponse(
        "dashboard_parent.html",
        {
            "request": request,
            "parent": parent,
            "pid": pid,
            "family_code": family_code,
        },
    )

@router.post("/{pid}/family/create")
def create_family_route(
    pid: int,
    family_name: str = Form(...),
    db: Session = Depends(get_db),
):

    parent = db.get(Users, pid)
    if not parent or parent.role != RoleEnum.parent:
        return RedirectResponse("/login", status_code=303)
    n = (family_name or "").strip()
    if not (1 <= len(n) <= 80):
        return RedirectResponse(f"/parent/dashboard/{pid}?err=bad_name", status_code=303)

    existing = db.query(Family).filter(Family.owner_parent_id == pid).first()
    if existing:
        return RedirectResponse(
            f"/parent/dashboard/{pid}?ok=already_have&code={existing.code}", status_code=303
        )

    fam = create_family(db, parent_id=pid, family_name=n)
    return RedirectResponse(
        url=f"/parent/dashboard/{pid}?ok=family_created&code={fam.code}",
        status_code=303
    )
