from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from config import get_db
from tables import users, tasks, submissions, rewards
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

@router.get("/dashboard/{pid}")
def dashboard_parent(request: Request, pid: int, db: Session = Depends(get_db)):
    parent = db.get(users.Users, pid)
    kids = db.query(users.Users).filter(users.Users.role == "kid").all()
    tasks_list = db.query(tasks.Task).filter(tasks.Task.parent_id == pid).all()
    rewards_list = db.query(rewards.Reward).all()
    notis = db.query(Notification).filter(Notification.to_user_id == pid).order_by(Notification.created_at.desc()).limit(20).all()
    pending_redeems = db.query(RewardRedeem).filter(RewardRedeem.status == RedeemStatus.pending).all()
    uc = unread_count(db, pid)
    return templates.TemplateResponse("dashboard_parent.html", {
        "request": request, "parent": parent, "kids": kids, "tasks": tasks_list,
        "rewards": rewards_list, "role": "parent", "pid": pid,
        "notis": notis, "pending_redeems": pending_redeems, "unread": uc
    })

@router.post("/task/create")
def create_task(title: str = Form(...), description: str = Form(""), points: int = Form(...),
                parent_id: int = Form(...), kid_id: int = Form(...), db: Session = Depends(get_db)):
    t = tasks.Task(title=title, description=description, points=points, parent_id=parent_id, kid_id=kid_id)
    db.add(t); db.commit()
    add_log(db, "task_create", parent_id, "tasks", t.id, {"points": points})
    return RedirectResponse(f"/parent/dashboard/{parent_id}", status_code=303)

@router.get("/submissions/{pid}")
def review_page(request: Request, pid: int, db: Session = Depends(get_db)):
    subs = db.query(submissions.Submission).join(tasks.Task).filter(tasks.Task.parent_id == pid).all()
    notis = db.query(Notification).filter(Notification.to_user_id == pid).order_by(Notification.created_at.desc()).limit(20).all()
    uc = unread_count(db, pid)
    return templates.TemplateResponse("submissions_parent.html", {"request": request, "subs": subs, "pid": pid, "role": "parent", "unread": uc, "notis": notis})

@router.post("/submission/decision/{sid}")
def decide_submission(sid: int, pid: int = Form(...), approve: str = Form(...), db: Session = Depends(get_db)):
    sub = db.get(submissions.Submission, sid)
    if not sub: return RedirectResponse(f"/parent/submissions/{pid}", status_code=303)
    task = db.get(tasks.Task, sub.task_id)
    kid = db.get(users.Users, sub.kid_id)

    if approve == "yes":
        sub.status = "approved"
        kid.points += task.points
        push_noti(db, to_user_id=kid.id, actor_user_id=pid,
                  type=NotiType.submission_approved, entity="submission", entity_id=sub.id,
                  message=f"พ่อแม่อนุมัติงาน: {task.title} +{task.points} แต้ม")
        add_log(db, "submission_approve", pid, "submissions", sub.id, {"status": sub.status})
    else:
        sub.status = "rejected"
        push_noti(db, to_user_id=kid.id, actor_user_id=pid,
                  type=NotiType.submission_rejected, entity="submission", entity_id=sub.id,
                  message=f"พ่อแม่ไม่อนุมัติงาน: {task.title}")
        add_log(db, "submission_reject", pid, "submissions", sub.id, {"status": sub.status})

    sub.reviewed_at = datetime.datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/parent/submissions/{pid}", status_code=303)

@router.post("/reward/add")
def add_reward(name: str = Form(...), cost: int = Form(...), description: str = Form(""),
               image: UploadFile = File(None), db: Session = Depends(get_db)):
    path = save_file(image, "rewards") if image else None
    r = rewards.Reward(name=name, description=description, cost=cost, image_path=path)
    db.add(r); db.commit()
    add_log(db, "reward_create", actor_id=0, target_table="rewards", target_id=r.id, details={"cost": cost})
    return RedirectResponse("/", status_code=303)

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
