from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from config import get_db, templates
from tables import users
from tables.tasks import Task, TaskStatus
from tables.submissions import Submission

router = APIRouter(prefix="/parent", tags=["Parent History"])

@router.get("/history/{pid}", response_class=HTMLResponse, name="parent_history_page")
def parent_history_page(pid: int, request: Request, db: Session = Depends(get_db)):
    parent = db.get(users.Users, pid)
    if not parent:
        return RedirectResponse("/login", status_code=303)

    tasks_done = (
        db.query(Task)
          .filter(Task.parent_id == pid, Task.status.in_([TaskStatus.approved, TaskStatus.rejected]))
          .order_by(Task.completed_at.desc().nullslast(), Task.created_at.desc())
          .all()
    )

    status_map = {
        TaskStatus.approved: "เสร็จแล้ว",
        TaskStatus.rejected: "ไม่อนุมัติ",
        TaskStatus.submitted: "รอตรวจ",
        TaskStatus.assigned: "งานใหม่",
    }
    
