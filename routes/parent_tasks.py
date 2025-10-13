from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from config import get_db
from tables.tasks import Task, TaskStatus
from tables.submissions import Submission, SubmissionStatus
from tables.rewards import Reward
from tables.reward_redeems import RewardRedeem, RedeemStatus
from utils.family import is_same_family
from datetime import datetime

router = APIRouter(prefix="/parent", tags=["Parent Tasks/Rewards"])

@router.post("/{pid}/task/create")
def create_task(pid: int, kid_id: int = Form(...), title: str = Form(...),
                description: str = Form(""), points: int = Form(...), db: Session = Depends(get_db)):
    if not is_same_family(db, parent_id=pid, kid_id=kid_id):
        return RedirectResponse(f"/parent/dashboard/{pid}?err=not_in_family", status_code=303)
    t = Task(title=title.strip(), description=description.strip(), points=points, parent_id=pid, kid_id=kid_id)
    db.add(t); db.commit()
    return RedirectResponse(f"/parent/dashboard/{pid}?ok=task_created", status_code=303)

@router.post("/{pid}/submission/decision/{sid}")
def decide_submission(pid: int, sid: int, approve: str = Form(...), db: Session = Depends(get_db)):
    sub = db.get(Submission, sid)
    if not sub: return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)
    task = db.get(Task, sub.task_id)
    if not task or task.parent_id != pid:
        return RedirectResponse(f"/parent/dashboard/{pid}?err=forbidden", status_code=303)
    if approve == "yes":
        sub.status = SubmissionStatus.approved; task.status = TaskStatus.approved
    else:
        sub.status = SubmissionStatus.rejected; task.status = TaskStatus.rejected
    sub.reviewed_at = datetime.utcnow()
    db.commit()
    db.delete(sub); db.commit()  # กันส่งซ้ำ
    return RedirectResponse(f"/parent/dashboard/{pid}?ok=reviewed", status_code=303)

@router.post("/{pid}/reward/add")
def add_reward(pid: int, name: str = Form(...), cost: int = Form(...),
               description: str = Form(""), db: Session = Depends(get_db)):
    r = Reward(parent_id=pid, name=name.strip(), description=description.strip(), cost=cost)
    db.add(r); db.commit()
    return RedirectResponse(f"/parent/dashboard/{pid}?ok=reward_added", status_code=303)

@router.post("/{pid}/redeem/decision/{rid}")
def decide_redeem(pid: int, rid: int, approve: str = Form(...), db: Session = Depends(get_db)):
    rr = db.get(RewardRedeem, rid)
    if not rr: return RedirectResponse(f"/parent/dashboard/{pid}", status_code=303)
    rr.status = RedeemStatus.approved if approve == "yes" else RedeemStatus.rejected
    rr.reviewed_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/parent/dashboard/{pid}?ok=redeem_reviewed", status_code=303)