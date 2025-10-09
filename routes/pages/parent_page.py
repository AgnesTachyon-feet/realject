from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from tables.notifications import Notification
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from config import get_db
from tables.tasks import Task, TaskStatus
from tables import users, tasks, submissions, rewards
import secrets
from tables.families import Family, FamilyMember
from tables.reward_redeems import RewardRedeem, RedeemStatus
from tables.notifications import NotiType, Notification
from core.notify import push_noti, unread_count
from core.logger import add_log
import os, shutil, uuid, datetime

router = APIRouter(prefix="/parent", tags=["Parent Pages"])
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(os.path.join(UPLOAD_DIR, "rewards"), exist_ok=True)

def save_file(file: UploadFile, subdir: str):
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, subdir, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return path

@router.post("/notifications/clear/{pid}")
def clear_parent_notifications(pid: int, db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.to_user_id == pid,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)

@router.post("/notifications/clear/{pid}")
def clear_parent_notifications(pid: int, db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.to_user_id == pid,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)
    
@router.get("/dashboard/{pid}")
def dashboard_parent(request: Request, pid: int, db: Session = Depends(get_db), code: str = None, err: str = None, ok: str = None):
    fam_ids = [fm.family_id for fm in db.query(FamilyMember).filter(
        FamilyMember.user_id == pid, FamilyMember.role == "parent"
    ).all()]

    kid_ids = [fm.user_id for fm in db.query(FamilyMember).filter(
        FamilyMember.family_id.in_(fam_ids), FamilyMember.role == "kid"
    ).all()]

    kids = db.query(users.Users).filter(users.Users.id.in_(kid_ids)).all()
    tasks_list = db.query(tasks.Task).filter(tasks.Task.parent_id == pid).all()
    rewards_list = db.query(rewards.Reward).all()
    return templates.TemplateResponse("dashboard_parent.html", {
        "request": request, "parent": db.get(users.Users, pid),
        "kids": kids, "tasks": tasks_list, "rewards": rewards_list,
        "role": "parent", "pid": pid,
        "new_family_code": code, "err": err, "ok": ok
    })

def is_in_same_family(db, parent_id: int, kid_id: int) -> bool:
    fam_ids = [fm.family_id for fm in db.query(FamilyMember).filter(
        FamilyMember.user_id == parent_id, FamilyMember.role == "parent"
    ).all()]
    if not fam_ids:
        return False
    return db.query(FamilyMember).filter(
        FamilyMember.user_id == kid_id,
        FamilyMember.role == "kid",
        FamilyMember.family_id.in_(fam_ids)
    ).count() > 0

@router.post("/family/create")
def create_family(pid: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    code = secrets.token_hex(3)  # โค้ดเชิญ
    fam = Family(name=name, code=code, owner_parent_id=pid)
    db.add(fam); db.commit()
    db.add(FamilyMember(family_id=fam.id, user_id=pid, role="parent")); db.commit()
    add_log(db, "family_create", pid, "families", fam.id, {"name": name})
    return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)

@router.post("/family/add-kid")
def add_kid_to_family(pid: int = Form(...), family_code: str = Form(...), kid_username: str = Form(...),
                      db: Session = Depends(get_db)):
    fam = db.query(Family).filter(Family.code == family_code).first()
    kid = db.query(users.Users).filter(users.Users.username == kid_username, users.Users.role == "kid").first()
    if not fam or not kid:
        return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)
    db.add(FamilyMember(family_id=fam.id, user_id=kid.id, role="kid")); db.commit()
    add_log(db, "family_add_kid", pid, "families", fam.id, {"kid": kid_username})
    return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)

@router.post("/task/create")
def create_task(title: str = Form(...), description: str = Form(""), points: int = Form(...),
                parent_id: int = Form(...), kid_id: int = Form(...), db: Session = Depends(get_db)):

    if not is_in_same_family(db, parent_id, kid_id):
        add_log(db, "task_create_denied", parent_id, "tasks", 0, {"kid_id": kid_id, "reason": "not_in_same_family"})
        return RedirectResponse(f"/parent/dashboard/{parent_id}?err=not_in_family", status_code=303)

    t = tasks.Task(title=title, description=description, points=points, parent_id=parent_id, kid_id=kid_id)
    db.add(t); db.commit()
    add_log(db, "task_create", parent_id, "tasks", t.id, {"points": points, "kid_id": kid_id})
    return RedirectResponse(f"/parent/dashboard/{parent_id}?ok=task_created", status_code=303)


@router.get("/submissions/{pid}")
def review_page(request: Request, pid: int, db: Session = Depends(get_db)):
    subs = db.query(submissions.Submission).join(tasks.Task).filter(tasks.Task.parent_id == pid).all()
    notis = db.query(Notification).filter(Notification.to_user_id == pid).order_by(Notification.created_at.desc()).limit(20).all()
    uc = unread_count(db, pid)
    return templates.TemplateResponse("submissions_parent.html", {"request": request, "subs": subs, "pid": pid, "role": "parent", "unread": uc, "notis": notis})

@router.post("/submission/decision/{sid}")
def decide_submission(
    sid: int,
    pid: int = Form(...),
    approve: str = Form(...),
    db: Session = Depends(get_db),
):
    sub = db.get(submissions.Submission, sid)
    if not sub:
        return RedirectResponse(f"/parent/submissions/{pid}", status_code=303)

    task = db.get(tasks.Task, sub.task_id)
    kid  = db.get(users.Users, sub.kid_id)

    if approve == "yes":
        sub.status = "approved"
        kid.points += task.points
        task.status = TaskStatus.approved

        push_noti(
            db, to_user_id=kid.id, actor_user_id=pid,
            type=NotiType.submission_approved,
            entity="submission", entity_id=sub.id,
            message=f"พ่อแม่อนุมัติงาน: {task.title} +{task.points} แต้ม",
        )
        add_log(db, "submission_approve", pid, "submissions", sub.id, {"status": sub.status})

    else:
        # ปฏิเสธ: เปิดงานให้เด็กเห็นอีกครั้ง
        sub.status = "rejected"
        task.status = TaskStatus.rejected

        push_noti(
            db, to_user_id=kid.id, actor_user_id=pid,
            type=NotiType.submission_rejected,
            entity="submission", entity_id=sub.id,
            message=f"พ่อแม่ไม่อนุมัติงาน: {task.title}",
        )
        add_log(db, "submission_reject", pid, "submissions", sub.id, {"status": sub.status})

    sub.reviewed_at = datetime.datetime.utcnow()

    db.delete(sub)
    db.commit()
    add_log(db, "submission_deleted", pid, "submissions", sid, {"reason": "review_completed"})

    return RedirectResponse(f"/parent/submissions/{pid}", status_code=303)

@router.post("/reward/add")
def add_reward(name: str = Form(...), cost: int = Form(...), description: str = Form(""),
               image: UploadFile = File(None), parent_id: int = Form(...),  # 👈 รับ parent_id
               db: Session = Depends(get_db)):
    path = save_file(image, "rewards") if image else None
    r = rewards.Reward(name=name, description=description, cost=cost, image_path=path)
    db.add(r); db.commit()
    add_log(db, "reward_create", actor_id=parent_id, target_table="rewards", target_id=r.id, details={"cost": cost})
    return RedirectResponse(f"/parent/dashboard/{parent_id}", status_code=303) 

@router.post("/redeem/decision/{redeem_id}")
def decide_redeem(redeem_id: int, pid: int = Form(...), approve: str = Form(...), db: Session = Depends(get_db)):
    rr = db.get(RewardRedeem, redeem_id)
    if not rr: return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)

    reward = db.get(rewards.Reward, rr.reward_id)
    kid = db.get(users.Users, rr.kid_id)

    if approve == "yes":
        if kid.points < reward.cost:
            rr.status = RedeemStatus.rejected
            push_noti(db, to_user_id=kid.id, actor_user_id=pid, type=NotiType.reward_redeem_rejected,
                      entity="reward_redeem", entity_id=rr.id, message=f"แต้มไม่พอ แลก {reward.name} ไม่สำเร็จ")
            add_log(db, "reward_redeem_reject", pid, "reward_redeems", rr.id, {"reason": "insufficient_points"})
        else:
            kid.points -= reward.cost
            rr.status = RedeemStatus.approved
            push_noti(db, to_user_id=kid.id, actor_user_id=pid, type=NotiType.reward_redeem_approved,
                      entity="reward_redeem", entity_id=rr.id, message=f"อนุมัติแลก {reward.name} -{reward.cost} แต้ม")
            add_log(db, "reward_redeem_approve", pid, "reward_redeems", rr.id, {"cost": reward.cost})
    else:
        rr.status = RedeemStatus.rejected
        push_noti(db, to_user_id=kid.id, actor_user_id=pid, type=NotiType.reward_redeem_rejected,
                  entity="reward_redeem", entity_id=rr.id, message=f"ปฏิเสธการแลก {reward.name}")
        add_log(db, "reward_redeem_reject", pid, "reward_redeems", rr.id, {"status": rr.status})

    rr.reviewed_at = datetime.datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)
