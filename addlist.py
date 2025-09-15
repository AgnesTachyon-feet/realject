from typing import List, Optional
from datetime import datetime, date
import os

from fastapi import FastAPI, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, relationship
import enum

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/child_rewards")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

app = FastAPI(title="Child Rewards - Tasks Feature")

# -----------------------------
# Models
# -----------------------------
class RoleEnum(str, enum.Enum):
    parent = "parent"
    child = "child"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    role = Column(SAEnum(RoleEnum), nullable=False)
    points = Column(Integer, default=0, nullable=False)

    # relationships
    parent_children = relationship("ParentChild", back_populates="parent", foreign_keys="ParentChild.parent_id")
    child_parents = relationship("ParentChild", back_populates="child", foreign_keys="ParentChild.child_id")


class ParentChild(Base):
    __tablename__ = "parent_child"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    parent = relationship("User", foreign_keys=[parent_id], back_populates="parent_children")
    child = relationship("User", foreign_keys=[child_id], back_populates="child_parents")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    points = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship("User")
    submissions = relationship("Submission", back_populates="task")


class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    photo_url = Column(String(1024), nullable=True)
    comment = Column(Text, nullable=True)
    status = Column(SAEnum(SubmissionStatus), default=SubmissionStatus.pending)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    task = relationship("Task", back_populates="submissions")
    child = relationship("User", foreign_keys=[child_id])

# -----------------------------
# Pydantic Schemas
# -----------------------------
class TaskCreate(BaseModel):
    title: str = Field(..., example="เก็บห้อง")
    description: Optional[str] = None
    due_date: Optional[date] = None
    points: int = Field(..., ge=0)


class TaskRead(BaseModel):
    id: int
    parent_id: int
    title: str
    description: Optional[str]
    due_date: Optional[date]
    points: int
    created_at: datetime

    class Config:
        orm_mode = True


class SubmissionCreate(BaseModel):
    photo_url: Optional[str] = None
    comment: Optional[str] = None


class SubmissionRead(BaseModel):
    id: int
    task_id: int
    child_id: int
    photo_url: Optional[str]
    comment: Optional[str]
    status: SubmissionStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    reviewer_id: Optional[int]

    class Config:
        orm_mode = True


class SubmissionReview(BaseModel):
    approve: bool
    reviewer_comment: Optional[str] = None

# -----------------------------
# Dependencies
# -----------------------------
from typing import AsyncGenerator
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(x_user_id: Optional[str] = Header(None), x_user_role: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)) -> User:
    """Simple demo dependency. In production, replace with real auth (JWT/OAuth2).
    Pass headers: X-User-Id and X-User-Role ('parent' or 'child').
    """
    if x_user_id is None or x_user_role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detaihl="Missing X-User-Id or X-User-Role headers")
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id")

    q = await db.get(User, user_id)
    if not q:
        raise HTTPException(status_code=404, detail="User not found")
    if q.role.value != x_user_role:
        raise HTTPException(status_code=403, detail="Role mismatch")
    return q

# -----------------------------
# Utility functions
# -----------------------------
async def is_parent_of(db: AsyncSession, parent_id: int, child_id: int) -> bool:
    from sqlalchemy import select
    res = await db.execute(select(ParentChild).where(ParentChild.parent_id == parent_id, ParentChild.child_id == child_id))
    found = res.scalar_one_or_none()
    return found is not None

# -----------------------------
# Routes - Tasks
# -----------------------------
@app.post("/tasks/", response_model=TaskRead)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.parent:
        raise HTTPException(status_code=403, detail="Only parents can create tasks")
    task = Task(
        parent_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        points=task_in.points,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@app.get("/tasks/", response_model=List[TaskRead])
async def list_tasks(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import select
    # If child -> show tasks from their parents
    if current_user.role == RoleEnum.child:
        # find parent ids
        res = await db.execute(select(ParentChild.parent_id).where(ParentChild.child_id == current_user.id))
        parent_ids = [row[0] for row in res.fetchall()]
        if not parent_ids:
            return []
        res = await db.execute(select(Task).where(Task.parent_id.in_(parent_ids)))
        tasks = res.scalars().all()
        return tasks
    else:
        # parent -> show tasks they created
        res = await db.execute(select(Task).where(Task.parent_id == current_user.id))
        tasks = res.scalars().all()
        return tasks


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Authorization: parent who created it or a child whose parent created it
    if current_user.role == RoleEnum.parent and task.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    if current_user.role == RoleEnum.child:
        allowed = await is_parent_of(db, task.parent_id, current_user.id)
        if not allowed:
            raise HTTPException(status_code=403, detail="Not allowed")
    return task

# -----------------------------
# Routes - Submissions
# -----------------------------
@app.post("/tasks/{task_id}/submit", response_model=SubmissionRead)
async def submit_task(task_id: int, submission_in: SubmissionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.child:
        raise HTTPException(status_code=403, detail="Only children can submit tasks")
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # check that the task belongs to one of child's parents
    allowed = await is_parent_of(db, task.parent_id, current_user.id)
    if not allowed:
        raise HTTPException(status_code=403, detail="Not allowed to submit this task")
    submission = Submission(
        task_id=task.id,
        child_id=current_user.id,
        photo_url=submission_in.photo_url,
        comment=submission_in.comment,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    # TODO: trigger notification to parent(s)h
    return submission


@app.get("/submissions/parent", response_model=List[SubmissionRead])
async def list_submissions_for_parent(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.parent:
        raise HTTPException(status_code=403, detail="Only parents can view this")
    from sqlalchemy import select
    # get submissions for tasks created by this parent
    res = await db.execute(select(Submission).join(Task).where(Task.parent_id == current_user.id))
    subs = res.scalars().all()
    return subs


@app.post("/submissions/{submission_id}/review", response_model=SubmissionRead)
async def review_submission(submission_id: int, review: SubmissionReview, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.parent:
        raise HTTPException(status_code=403, detail="Only parents can review submissions")
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    task = await db.get(Task, submission.task_id)
    if task.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to review this submission")

    if submission.status != SubmissionStatus.pending:
        raise HTTPException(status_code=400, detail="Submission already reviewed")

    submission.reviewed_at = datetime.utcnow()
    submission.reviewer_id = current_user.id
    if review.approve:
        submission.status = SubmissionStatus.approved
        # give points to child
        child = await db.get(User, submission.child_id)
        child.points += task.points
        db.add(child)
        await db.commit()
        await db.refresh(child)
    else:
        submission.status = SubmissionStatus.rejected
        db.add(submission)
        await db.commit()
    await db.refresh(submission)
    # TODO: notify child of result
    return submission

# -----------------------------
# Startup utility - create tables (for demo)
# -----------------------------
@app.on_event("startup")
async def on_startup():
    # Create tables if they don't exist (good for demo; in prod use migrations)
    async with engine.begin() as conn:h
        await conn.run_sync(Base.metadata.create_all)

# -----------------------------
# Notes:
# - Authentication here is simplified: pass X-User-Id and X-User-Role headers.
# - photo_url is assumed to be a stored URL (you can integrate S3 or other storage for uploads).
# - Notifications are marked with TODO comments: integrate websockets, push notifications, or email.
# - Use alembic for proper database migrations in production.
# - Expand models (e.g., Rewards, Leaderboard) as needed.
# -----------------------------hh
