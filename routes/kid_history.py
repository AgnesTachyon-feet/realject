from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from config import get_db, templates
from tables.users import Users, RoleEnum
from tables.tasks import Task, TaskStatus
from tables.reward_redeems import RewardRedeem, RedeemStatus
from tables.rewards import Reward

router = APIRouter(prefix="/kid", tags=["Kid History"])

@router.get("/history/{kid_id}", response_class=HTMLResponse, name="kid_history_page")
def kid_history_page(kid_id: int, request: Request, db: Session = Depends(get_db)):
    kid = db.get(Users, kid_id)
    if not kid or kid.role != RoleEnum.kid:
        return RedirectResponse("/login", status_code=303)

    tasks_done = (
        db.query(Task)
          .filter(Task.kid_id == kid_id, Task.status == TaskStatus.approved)
          .order_by(desc(Task.completed_at.nullslast()), desc(Task.created_at))
          .all()
    )

    redeems_ok = (
        db.query(RewardRedeem, Reward)
          .join(Reward, Reward.id == RewardRedeem.reward_id)
          .filter(RewardRedeem.kid_id == kid_id, RewardRedeem.status == RedeemStatus.approved)
          .order_by(desc(RewardRedeem.reviewed_at.nullslast()), desc(RewardRedeem.created_at))
          .all()
    )

    tasks_view = [{
        "task_id": t.id,
        "title": t.title,
        "points": t.points or 0,
        "completed_at": t.completed_at.strftime("%d %b %Y %H:%M") if t.completed_at else "-",
    } for t in tasks_done]

    rewards_view = [{
        "name": rw.name,
        "cost": rw.cost,
        "approved_at": (rr.reviewed_at.strftime("%d %b %Y %H:%M") if rr.reviewed_at else "-")
    } for (rr, rw) in redeems_ok]

    total_points = (kid.points or 0)

    return templates.TemplateResponse("kid_history.html", {
        "request": request,
        "kid": kid,
        "total_points": total_points,
        "tasks": tasks_view,
        "redeems": rewards_view
    })
