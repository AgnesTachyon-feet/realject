from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, exists
import datetime, os, shutil, uuid
from config import get_db, templates
from tables.users import Users, RoleEnum
from tables.tasks import Task, TaskStatus
from tables.submissions import Submission
from tables.rewards import Reward
from tables.reward_redeems import RewardRedeem, RedeemStatus
from tables.families import FamilyMember, Family
from utils.family import join_family as join_family_util
from core.notify import toast

router = APIRouter(prefix="/kid", tags=["Kid Pages"])


@router.get("/dashboard/{kid_id}", response_class=HTMLResponse)
def dashboard_kid(kid_id: int, request: Request, db: Session = Depends(get_db)):
    kid = db.get(Users, kid_id)
    if not kid or kid.role != RoleEnum.kid:
        return RedirectResponse("/login", status_code=303)

    in_family = db.execute(
        select(exists().where(
            FamilyMember.user_id == kid_id,
            FamilyMember.family_id.isnot(None),
            FamilyMember.role == RoleEnum.kid
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
                TaskStatus.submitted
            ])
        ).order_by(Task.created_at.desc()).all()
    else:
        task_list = []
    count_new = db.query(Task).filter(Task.kid_id == kid_id, Task.status == TaskStatus.assigned).count()
    count_pending = db.query(Task).filter(Task.kid_id == kid_id, Task.status == TaskStatus.submitted).count()
    count_done = db.query(Task).filter(Task.kid_id == kid_id, Task.status == TaskStatus.approved).count()

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

    all_rewards = db.query(Reward).all() if in_family else []
    redeems = db.query(RewardRedeem).filter(RewardRedeem.kid_id == kid_id).all()
    taken_status = {r.reward_id: r.status for r in redeems}

    rewards_list = []
    for r in all_rewards:
        st = taken_status.get(r.id)
        if st in {RedeemStatus.pending, RedeemStatus.approved}:
            continue
        rewards_list.append(r)

    rewards_view = [{
        "id": r.id,
        "name": r.name,
        "description": r.description or "",
        "cost": r.cost,
        "image_path": getattr(r, "image_path", None),
    } for r in rewards_list]

    pending_rows = (
        db.query(RewardRedeem, Reward)
        .join(Reward, Reward.id == RewardRedeem.reward_id)
        .filter(RewardRedeem.kid_id == kid_id,
                RewardRedeem.status == RedeemStatus.pending)
        .order_by(RewardRedeem.created_at.desc())
        .all()
    )

    pending_rewards = [{
        "redeem_id": rr.id,
        "name": rw.name,
        "cost": rw.cost,
        "image_path": getattr(rw, "image_path", None),
        "requested_at": rr.created_at.strftime("%d %b %Y %H:%M")
    } for (rr, rw) in pending_rows]

    return templates.TemplateResponse("dashboard_kid.html", {
        "request": request,
        "kid": kid,
        "in_family": in_family,
        "family_name": family_name,
        "tasks": tasks_view,
        "rewards": rewards_view,
        "pending_rewards": pending_rewards,
        "count_new": count_new,
        "count_pending": count_pending,
        "count_done": count_done,
    })


@router.post("/join-family")
def kid_join_family(kid_id: int = Form(...),
                    family_code: str = Form(...),
                    db: Session = Depends(get_db)):
    try:
        join_family_util(db, kid_id=kid_id, code=family_code)
        return RedirectResponse(f"/kid/dashboard/{kid_id}?ok=joined", status_code=303)
    except ValueError:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=invalid_code", status_code=303)

def _save_file(file: UploadFile):
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return path


@router.post("/submit/{task_id}")
def submit_task(task_id: int,
                kid_id: int = Form(...),
                note: str = Form(""),
                evidence: UploadFile = File(None),
                db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task or task.kid_id != kid_id:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=no_task", status_code=303)
    if task.status not in [TaskStatus.assigned, TaskStatus.rejected]:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=bad_status", status_code=303)

    path = _save_file(evidence) if evidence else None
    sub = Submission(task_id=task_id, kid_id=kid_id,
                     message=note.strip(), evidence_path=path)
    db.add(sub)
    task.status = TaskStatus.submitted
    db.commit()
    toast("ส่งงานแล้ว",f"ภารกิจ {task.title} ถูกส่งเรียบร้อยแล้ว")
    return RedirectResponse(f"/kid/dashboard/{kid_id}?ok=submitted", status_code=303)

@router.post("/redeem/{reward_id}")
def redeem_reward(reward_id: int,
                  kid_id: int = Form(...),
                  db: Session = Depends(get_db)):
    dup = db.query(RewardRedeem).filter(
        RewardRedeem.kid_id == kid_id,
        RewardRedeem.reward_id == reward_id,
        RewardRedeem.status == RedeemStatus.pending
    ).first()
    if dup:
        return RedirectResponse(f"/kid/dashboard/{kid_id}?err=dup_redeem", status_code=303)

    rr = RewardRedeem(reward_id=reward_id, kid_id=kid_id)
    db.add(rr)
    db.commit()
    return RedirectResponse(f"/kid/dashboard/{kid_id}?ok=redeem_requested", status_code=303)