from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from config import get_db, templates
from tables.users import Users, RoleEnum
from tables.families import Family, FamilyMember
from tables.rewards import Reward
from tables.tasks import Task, TaskStatus
from tables.submissions import Submission
from tables.reward_redeems import RewardRedeem, RedeemStatus
from utils.family import create_family
import datetime

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

@router.get("/submissions/{pid}", response_class=HTMLResponse, name="parent_review_page")
def review_page(pid: int, request: Request, db: Session = Depends(get_db)):
    parent = db.get(Users, pid)
    if not parent or parent.role != RoleEnum.parent:
        return RedirectResponse("/login", status_code=303)

    # ดึง submission ที่รอและเป็นงานของ parent คนนี้ (join แค่ใช้กรอง ไม่พึ่ง s.task)
    subs = (
        db.query(Submission)
        .join(Task, Task.id == Submission.task_id)
        .filter(Task.parent_id == pid, Submission.status == "pending")
        .order_by(Submission.created_at.desc())
        .all()
    )

    items = []
    for s in subs:
        t = db.get(Task, s.task_id)         # โหลด Task ตรงๆ แทน s.task
        kid = db.get(Users, s.kid_id)       # โหลด Kid ตรงๆ
        items.append({
            "submission_id": s.id,
            "task_id": s.task_id,
            "task_title": t.title if t else "",
            "task_points": t.points if t else 0,
            "kid_id": s.kid_id,
            "kid_name": kid.first_name if kid else "Kid",
            "message": s.message or "",
            "evidence_path": s.evidence_path,
            "submitted_at": s.created_at.strftime("%d %b %Y %H:%M"),
        })

    return templates.TemplateResponse("submissions_parent.html", {
        "request": request,
        "parent": parent,
        "pid": pid,
        "items": items
    })


# ปุ่มอนุมัติ/ปฏิเสธ
@router.post("/submission/decision/{sid}", name="parent_decide_submission")
def decide_submission(
    sid: int,
    pid: int = Form(...),
    approve: str = Form(...),
    db: Session = Depends(get_db),
):
    sub = db.get(Submission, sid)
    if not sub:
        return RedirectResponse(f"/parent/submissions/{pid}?err=no_submission", status_code=303)

    task = db.get(Task, sub.task_id)
    kid  = db.get(Users, sub.kid_id)

    if not task or task.parent_id != pid:
        return RedirectResponse(f"/parent/submissions/{pid}?err=unauthorized", status_code=303)

    if approve == "yes":
        if kid:
            kid.points = (kid.points or 0) + (task.points or 0)
        task.status = TaskStatus.approved
        sub.status = "approved"
    else:
        task.status = TaskStatus.rejected
        sub.status = "rejected"

    sub.reviewed_at = datetime.datetime.utcnow()

    db.delete(sub)
    db.commit()

    return RedirectResponse(f"/parent/submissions/{pid}?ok=done", status_code=303)