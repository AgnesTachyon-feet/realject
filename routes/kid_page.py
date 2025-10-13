# routes/kid_page.py
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, exists
from datetime import datetime
import os, uuid, shutil

from config import get_db, templates
from tables.users import Users, RoleEnum
from tables.tasks import Task, TaskStatus
from tables.submissions import Submission
from tables.rewards import Reward
from tables.reward_redeems import RewardRedeem, RedeemStatus
from tables.families import FamilyMember, Family
from utils.family import join_family as join_family_util

router = APIRouter(prefix="/kid", tags=["Kid Pages"])

# === เพิ่ม helper เซฟไฟล์ (ถ้าอยากใช้ utils.files ก็เปลี่ยนตามคอมเมนต์ด้านล่าง) ===
UPLOAD_DIR = "static/uploads/submissions"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _save_file(upload: UploadFile) -> str | None:
    if not upload:
        return None
    filename = f"{uuid.uuid4().hex}_{upload.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return path
# ถ้าอยากใช้ไฟล์รวมแทน:
# from utils.files import save_file
# แล้วเปลี่ยนตอนใช้งานเป็น: path = save_file(evidence, subdir="submissions")

@router.get("/dashboard/{kid_id}", response_class=HTMLResponse, name="kid_dashboard")
def dashboard_kid(kid_id: int, request: Request, db: Session = Depends(get_db)):
    kid = db.get(Users, kid_id)
    if not kid or kid.role != RoleEnum.kid:
        return RedirectResponse("/login", status_code=303)

    in_family = db.execute(
        select(exists().where(
            FamilyMember.user_id == kid_id,
            FamilyMember.family_id.isnot(None),
            # ถ้า column role เป็น PGEnum(RoleEnum) ใช้แบบนี้:
            FamilyMember.role == RoleEnum.kid
            # ถ้า column role เป็น String ค่อยใช้: FamilyMember.role == RoleEnum.kid.value
        ))
    ).scalar()

    family_name = None
    if in_family:
        fam = db.query(Family).join(FamilyMember, FamilyMember.family_id == Family.id)\
                              .filter(FamilyMember.user_id == kid_id).first()
        family_name = fam.name if fam else None

        task_list = db.query(Task).filter(
            Task.kid_id == kid_id,
            Task.status.in_([
                TaskStatus.assigned,
                TaskStatus.rejected,
                TaskStatus.submitted,
                TaskStatus.approved
            ])
        ).order_by(Task.created_at.desc()).all()
    else:
        task_list = []

    count_new     = sum(1 for t in task_list if t.status == TaskStatus.assigned)
    count_pending = sum(1 for t in task_list if t.status == TaskStatus.submitted)
    count_done    = sum(1 for t in task_list if t.status == TaskStatus.approved)

    status_map = {
        TaskStatus.assigned: "งานใหม่",
        TaskStatus.submitted: "รอตรวจ",
        TaskStatus.approved: "เสร็จแล้ว",
        TaskStatus.rejected: "ไม่อนุมัติ",
    }
    tasks_view = [{
        "id": t.id,
        "title": t.title,
        "description": t.description or "",
        "points": t.points,
        "status": t.status.value,
        "status_display": status_map[t.status],
        "created_at": t.created_at.strftime("%d %b %Y %H:%M"),
    } for t in task_list]

    rewards_list = db.query(Reward).all() if in_family else []
    rewards_view = [{
        "id": r.id, "name": r.name,
        "description": r.description or "",
        "cost": r.cost,
        "remaining": getattr(r, "remaining", None)
    } for r in rewards_list]

    print(f"[kid_dashboard] kid_id={kid_id} in_family={in_family} tasks={len(tasks_view)}")

    return templates.TemplateResponse("dashboard_kid.html", {
        "request": request,
        "kid": kid,
        "in_family": in_family,
        "family_name": family_name,
        "tasks": tasks_view,
        "rewards": rewards_view,
        "count_new": count_new,
        "count_pending": count_pending,
        "count_done": count_done,
    })

@router.post("/join-family", name="kid_join_family")
def kid_join_family(
    kid_id: int = Form(...),
    family_code: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        join_family_util(db, kid_id=kid_id, code=family_code)
        return RedirectResponse(f"/kid/dashboard/{kid_id}?ok=joined", status_code=303)
    except ValueError:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=invalid_code", status_code=303)

@router.post("/submit/{task_id}", name="kid_submit_task")
def submit_task(
    task_id: int,
    kid_id: int = Form(...),
    note: str = Form(""),
    evidence: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if not task or task.kid_id != kid_id:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=no_task", status_code=303)

    if task.status not in [TaskStatus.assigned, TaskStatus.rejected]:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=bad_status", status_code=303)

    path = _save_file(evidence) if evidence else None
    # ถ้าใช้ utils.files: path = save_file(evidence, subdir="submissions") if evidence else None

    sub = Submission(task_id=task_id, kid_id=kid_id, message=note.strip(), evidence_path=path)
    db.add(sub)
    task.status = TaskStatus.submitted
    db.commit()
    return RedirectResponse(f"/kid/dashboard/{kid_id}?ok=submitted", status_code=303)

@router.post("/redeem/{reward_id}", name="kid_redeem_reward")
def redeem_reward(
    reward_id: int,
    kid_id: int = Form(...),
    db: Session = Depends(get_db),
):
    dup = db.query(RewardRedeem).filter(
        RewardRedeem.kid_id == kid_id,
        RewardRedeem.reward_id == reward_id,
        RewardRedeem.status == RedeemStatus.pending
    ).first()
    if dup:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=dup_redeem", status_code=303)

    rr = RewardRedeem(reward_id=reward_id, kid_id=kid_id)
    db.add(rr); db.commit()
    return RedirectResponse(f"/kid/dashboard/{kid_id}?ok=redeem_requested", status_code=303)