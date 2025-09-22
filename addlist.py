# main.py

"""
ส่วนนี้ของโปรแกรมกำหนดการเชื่อมต่อกับฐานข้อมูล PostgreSQL
และตั้งค่า SQLAlchemy engine, session และ Base สำหรับ ORM
คำอธิบายนี้มีความยาวเพื่ออธิบายว่าทำไมต้องมีส่วนนี้:
1) engine เป็นตัวกลางในการเชื่อมต่อกับฐานข้อมูล
2) sessionmaker จะสร้าง session สำหรับการทำ transaction แต่ละคำขอ
3) Base คือ declarative base ที่จะใช้ในการประกาศโมเดล ORM (ตาราง)
การมีส่วนนี้ทำให้โค้ดสามารถสื่อสารกับ PostgreSQL ผ่าน SQLAlchemy ORM ได้อย่างเป็นระบบ
"""
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import shutil
import uuid

# SQLAlchemy imports
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Enum,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
import enum

# -----------------------
# Database configuration
# -----------------------

# ตัวแปร DATABASE_URL ให้แก้เป็นของคุณก่อนรันแอป เช่น:
# postgresql+psycopg2://username:password@localhost:5432/yourdb
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:password@localhost:5432/mydb")

# สร้าง SQLAlchemy engine โดยใช้ DATABASE_URL ที่ระบุ
engine = create_engine(DATABASE_URL, echo=False, future=True)

# sessionmaker สร้าง session factory ที่จะใช้ภายใน dependency ของ FastAPI
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Declarative base สำหรับประกาศ ORM models (ตารางต่าง ๆ)
Base = declarative_base()

# -----------------------
# ORM Models (Database Tables)
# -----------------------

"""
ส่วนนี้ประกาศโมเดล ORM สำหรับตารางหลักที่เกี่ยวข้องกับระบบ Tasks/Missions
คำอธิบาย:
- User: เก็บข้อมูลผู้ใช้ทั้ง Parent และ Child (มี role แยกประเภท)
- Task: รายการภารกิจ ที่ parent สร้างและระบุ child ผู้รับ
- Submission: งานที่ child ส่งเป็นหลักฐาน (เก็บ path ของไฟล์)
- PointsHistory: ประวัติการให้แต้มเมื่อ submission ถูกอนุมัติ
- Notification: ข้อความแจ้งเตือนภายในระบบ (เก็บใน DB เพื่อให้ frontend ดึงมาแสดง)
การออกแบบนี้ทำให้เราจัดการข้อมูลสำคัญของ workflow ได้ครบถ้วน
"""

class UserRole(enum.Enum):
    parent = "parent"
    child = "child"

class SubmissionStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=True)  # placeholder; auth not implemented here
    profile_pic = Column(String(512), nullable=True)
    points = Column(Integer, default=0, nullable=False)

    # Relationships
    tasks_created = relationship("Task", back_populates="parent", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="child", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    points_history = relationship("PointsHistory", back_populates="child", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    points = Column(Integer, default=0, nullable=False)

    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent = relationship("User", foreign_keys=[parent_id], back_populates="tasks_created")
    # child relationship via child_id is not back_populates on User to avoid ambiguity
    submissions = relationship("Submission", back_populates="task", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    evidence_path = Column(String(1024), nullable=True)  # path to uploaded file
    message = Column(Text, nullable=True)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.pending, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="submissions")
    child = relationship("User", back_populates="submissions")


class PointsHistory(Base):
    __tablename__ = "points_history"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    points = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    child = relationship("User", back_populates="points_history")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


# -----------------------
# Create database tables
# -----------------------

"""
ส่วนนี้จะสร้างตารางทั้งหมดในฐานข้อมูลเมื่อโมดูลรัน (ถ้ายังไม่มี)
คำอธิบาย:
การเรียก Base.metadata.create_all() จะอ่าน declarative models ข้างต้นแล้วสร้างตารางใน PostgreSQL
ทำให้ developer ไม่ต้องเขียน SQL CREATE TABLE ด้วยตนเองในขั้นแรก
"""

Base.metadata.create_all(bind=engine)

# -----------------------
# FastAPI app configuration
# -----------------------

"""
ส่วนนี้สร้าง FastAPI application instance และตั้งค่า middleware เบื้องต้น
คำอธิบาย:
- instance ของ FastAPI จะเป็นจุดศูนย์กลางในการรับ HTTP requests และส่ง responses
- ตั้ง CORS เพื่อให้ frontend ที่รันบน domain อื่นสามารถเรียก API ได้ (ปรับ origin ตามต้องการ)
"""

app = FastAPI(title="Tasks/Missions API - Parent/Child System")

# ตั้งค่า CORS แบบพื้นฐาน (ปรับ origins เป็น domain ของคุณเมื่อ deploy จริง)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Dependency: DB session
# -----------------------

"""
ส่วนนี้เป็น dependency ของ FastAPI ที่สร้างและคืน session ของ SQLAlchemy
คำอธิบาย:
- ทุกครั้งที่ endpoint ต้องการเชื่อมต่อ DB ให้เรียก dependency นี้
- session จะถูกปิดเมื่อ request เสร็จสิ้นเพื่อป้องกัน connection leak
"""

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# Pydantic schemas (request / response models)
# -----------------------

"""
ส่วนนี้ประกาศ Pydantic models สำหรับรับ/ส่งข้อมูลผ่าน API
คำอธิบาย:
- จะช่วย validate input และกำหนดรูปแบบ JSON response ให้ชัดเจน
- ใช้ BaseModel จาก pydantic เพื่อให้สามารถใช้งานกับ FastAPI ได้ตรงตาม expected types
"""

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    points: int = 0
    parent_id: int
    child_id: int

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    points: int
    parent_id: int
    child_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class SubmissionCreate(BaseModel):
    task_id: int
    child_id: int
    message: Optional[str] = None

class SubmissionOut(BaseModel):
    id: int
    task_id: int
    child_id: int
    evidence_path: Optional[str]
    message: Optional[str]
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        orm_mode = True

class SubmissionDecision(BaseModel):
    parent_id: int
    approve: bool  # true = approve, false = reject
    comment: Optional[str] = None

class PointsOut(BaseModel):
    child_id: int
    total_points: int

    class Config:
        orm_mode = True

class PointsHistoryOut(BaseModel):
    id: int
    child_id: int
    task_id: Optional[int]
    points: int
    created_at: datetime

    class Config:
        orm_mode = True

# -----------------------
# Helper utilities
# -----------------------

"""
ส่วนนี้ประกอบด้วยฟังก์ชันย่อยที่ช่วยจัดการไฟล์และการสร้าง notification
คำอธิบาย:
- save_upload_file จะรับไฟล์ UploadFile จาก FastAPI และบันทึกลงโฟลเดอร์ uploads
- create_notification จะสร้างแถว notification ใน DB เพื่อให้ผู้ใช้เห็นการแจ้งเตือนภายในแอป
การแยกเป็นฟังก์ชันจะทำให้โค้ดส่วนหลักอ่านง่ายและลดการทำซ้ำของโค้ด
"""

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    """
    ฟังก์ชันนี้บันทึกไฟล์จาก UploadFile ลง path ที่กำหนด
    คำอธิบาย:
    - ใช้ shutil เพื่อเขียนไฟล์ทีละ chunk เพื่อไม่ให้กิน memory มาก
    - ชื่อไฟล์ถูกสร้าง unique โดยการรวม uuid เข้ากับ filename เพื่อป้องกันการชนกัน
    """
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

def create_notification(db: Session, user_id: int, message: str) -> Notification:
    """
    ฟังก์ชันนี้สร้าง notification ใหม่ในฐานข้อมูล
    คำอธิบาย:
    - เก็บ notification เพื่อให้ frontend สามารถดึงมาแสดงให้ผู้ใช้ได้
    - คืนค่า object ที่สร้างเพื่อให้สามารถใช้งานต่อใน flow ได้ (เช่น return response)
    """
    notification = Notification(user_id=user_id, message=message)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

# -----------------------
# API Endpoints for Tasks / Missions
# -----------------------

"""
Endpoint: POST /tasks/
คำอธิบาย:
- Endpoint นี้ใช้สำหรับให้ผู้ปกครอง (parent) สร้างภารกิจใหม่โดยระบุชื่อ คำอธิบาย วันครบกำหนด แต้มที่ให้
- รับข้อมูลในรูปแบบ JSON ที่ตรงกับ Pydantic model TaskCreate
- บันทึกภารกิจลงในตาราง tasks และคืนข้อมูลภารกิจที่สร้างแล้วกลับไป
"""
@app.post("/tasks/", response_model=TaskOut)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    # ตรวจสอบว่าผู้ปกครองและเด็กมีอยู่ในระบบ (เบื้องต้น)
    parent = db.get(User, task_in.parent_id)
    child = db.get(User, task_in.child_id)
    if not parent or parent.role != UserRole.parent:
        raise HTTPException(status_code=404, detail="Parent not found or wrong role")
    if not child or child.role != UserRole.child:
        raise HTTPException(status_code=404, detail="Child not found or wrong role")

    task = Task(
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        points=task_in.points,
        parent_id=task_in.parent_id,
        child_id=task_in.child_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # สร้าง notification ให้ child ว่ามีงานมอบหมาย
    create_notification(db, user_id=task_in.child_id, message=f"คุณได้รับภารกิจใหม่: {task.title}")

    return task

"""
Endpoint: GET /tasks/child/{child_id}
คำอธิบาย:
- Endpoint นี้ให้เด็ก (child) ดึงรายการภารกิจที่มอบหมายให้ตนเองทั้งหมด
- คืนค่าเป็น list ของ TaskOut ซึ่งประกอบด้วยข้อมูลภารกิจที่จำเป็นสำหรับ UI
- ใช้ child_id ใน path เพื่อระบุผู้ใช้ที่ต้องการดึงภารกิจ
"""
@app.get("/tasks/child/{child_id}", response_model=List[TaskOut])
def get_tasks_for_child(child_id: int, db: Session = Depends(get_db)):
    child = db.get(User, child_id)
    if not child or child.role != UserRole.child:
        raise HTTPException(status_code=404, detail="Child not found or wrong role")
    tasks = db.query(Task).filter(Task.child_id == child_id).order_by(Task.created_at.desc()).all()
    return tasks

"""
Endpoint: POST /submissions/ (multipart/form-data)
คำอธิบาย:
- Endpoint นี้ให้เด็กส่งงานสำหรับภารกิจโดยแนบไฟล์หลักฐาน (รูป) และข้อความประกอบ
- รับไฟล์ผ่าน UploadFile และข้อมูลอื่น ๆ ในรูปแบบ form fields
- บันทึกไฟล์ในโฟลเดอร์ uploads และสร้างแถว submission ใน DB
- สร้าง notification ถึง parent ว่ามีการส่งงานใหม่
"""
@app.post("/submissions/", response_model=SubmissionOut)
async def submit_task(
    task_id: int,
    child_id: int,
    message: Optional[str] = None,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # ตรวจสอบ task และ child
    task = db.get(Task, task_id)
    child = db.get(User, child_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not child or child.role != UserRole.child:
        raise HTTPException(status_code=404, detail="Child not found or wrong role")
    if task.child_id != child_id:
        raise HTTPException(status_code=400, detail="This task is not assigned to this child")

    # หากมีไฟล์แนบ บันทึกลง uploads และเก็บ path
    evidence_path = None
    if file:
        unique_suffix = uuid.uuid4().hex
        filename = f"{unique_suffix}_{file.filename}"
        dest_path = os.path.join(UPLOAD_DIR, filename)
        # save file
        save_upload_file(file, dest_path)
        evidence_path = dest_path

    submission = Submission(
        task_id=task_id,
        child_id=child_id,
        evidence_path=evidence_path,
        message=message,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # แจ้งผู้ปกครอง (parent) ว่ามีการส่งงานใหม่
    create_notification(db, user_id=task.parent_id, message=f"เด็กส่งงานสำหรับ: {task.title}")

    return submission

"""
Endpoint: GET /submissions/parent/{parent_id}
คำอธิบาย:
- Endpoint นี้ให้ผู้ปกครองดึงรายการ submission ของภารกิจที่ตนเป็นผู้สร้างทั้งหมด
- ประโยชน์คือผู้ปกครองสามารถดูหลักฐานที่เด็กส่งและตัดสินใจอนุมัติ/ปฏิเสธ
- คืนค่าเป็น list ของ SubmissionOut
"""
@app.get("/submissions/parent/{parent_id}", response_model=List[SubmissionOut])
def get_submissions_for_parent(parent_id: int, db: Session = Depends(get_db)):
    parent = db.get(User, parent_id)
    if not parent or parent.role != UserRole.parent:
        raise HTTPException(status_code=404, detail="Parent not found or wrong role")
    # join submissions -> tasks to filter by tasks created by this parent
    submissions = (
        db.query(Submission)
        .join(Task, Submission.task_id == Task.id)
        .filter(Task.parent_id == parent_id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    return submissions

"""
Endpoint: PATCH /submissions/{submission_id}/decision
คำอธิบาย:
- Endpoint นี้ใช้โดยผู้ปกครองเพื่อตัดสินใจ (อนุมัติ/ปฏิเสธ) งานที่เด็กส่ง
- เมื่ออนุมัติ: จะเพิ่มแต้มให้เด็กตามคะแนนของ Task, สร้าง PointsHistory และแจ้งเตือนเด็ก
- เมื่อปฏิเสธ: อัปเดตสถานะเป็น rejected และแจ้งเตือนเด็ก
- รับ body ตาม SubmissionDecision (parent_id, approve(bool), comment)
"""
@app.patch("/submissions/{submission_id}/decision", response_model=SubmissionOut)
def decide_submission(submission_id: int, decision: SubmissionDecision, db: Session = Depends(get_db)):
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    task = db.get(Task, submission.task_id)
    parent = db.get(User, decision.parent_id)
    if not parent or parent.role != UserRole.parent:
        raise HTTPException(status_code=404, detail="Parent not found or wrong role")
    if not task or task.parent_id != decision.parent_id:
        raise HTTPException(status_code=403, detail="You are not allowed to review this submission")

    # ตัดสินใจ
    if decision.approve:
        submission.status = SubmissionStatus.approved
        submission.reviewed_at = datetime.utcnow()

        # เพิ่มแต้มให้ child
        child = db.get(User, submission.child_id)
        points_to_add = task.points or 0
        child.points = (child.points or 0) + points_to_add

        # บันทึก history ของแต้ม
        points_history = PointsHistory(child_id=child.id, task_id=task.id, points=points_to_add)
        db.add(points_history)

        # สร้าง notification ให้เด็ก
        create_notification(db, user_id=child.id, message=f"งาน '{task.title}' ของคุณได้รับการอนุมัติ ได้รับ {points_to_add} แต้ม")
    else:
        submission.status = SubmissionStatus.rejected
        submission.reviewed_at = datetime.utcnow()
        # แจ้งเตือนเด็กว่าถูกปฏิเสธ
        create_notification(db, user_id=submission.child_id, message=f"งาน '{task.title}' ถูกปฏิเสธ: {decision.comment or ''}")

    db.commit()
    db.refresh(submission)
    return submission

"""
Endpoint: GET /points/{child_id}
คำอธิบาย:
- Endpoint นี้ให้ดึงแต้มปัจจุบันของเด็ก (total points) และคืนค่าในรูปแบบ PointsOut
- ใช้เมื่อ UI ต้องการแสดงคะแนนสะสมของเด็กที่หน้าโปรไฟล์หรือหน้าแลกรางวัล
"""
@app.get("/points/{child_id}", response_model=PointsOut)
def get_points(child_id: int, db: Session = Depends(get_db)):
    child = db.get(User, child_id)
    if not child or child.role != UserRole.child:
        raise HTTPException(status_code=404, detail="Child not found or wrong role")
    return PointsOut(child_id=child.id, total_points=child.points or 0)

"""
Endpoint: GET /points/{child_id}/history
คำอธิบาย:
- Endpoint นี้คืนประวัติการได้แต้มทั้งหมดของเด็กในรูปแบบรายการ PointsHistoryOut
- ใช้สำหรับหน้าแสดงประวัติการได้รับแต้ม (เพื่อให้เด็ก/ผู้ปกครองเห็นว่าได้แต้มจากงานใดบ้าง)
"""
@app.get("/points/{child_id}/history", response_model=List[PointsHistoryOut])
def get_points_history(child_id: int, db: Session = Depends(get_db)):
    child = db.get(User, child_id)
    if not child or child.role != UserRole.child:
        raise HTTPException(status_code=404, detail="Child not found or wrong role")
    histories = db.query(PointsHistory).filter(PointsHistory.child_id == child_id).order_by(PointsHistory.created_at.desc()).all()
    return histories

"""
Endpoint: GET /notifications/{user_id}
คำอธิบาย:
- Endpoint นี้ให้ผู้ใช้ดึงรายการ notification ที่เก็บไว้ในระบบ (ยังไม่มี push จริง)
- คืน list ของ notification เพื่อให้ frontend นำมาแสดงเป็น in-app notifications
"""
@app.get("/notifications/{user_id}")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    notes = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    # แปลงเป็น JSON-friendly
    result = [
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notes
    ]
    return {"notifications": result}

# -----------------------
# Utility endpoints for testing / seed data (optional)
# -----------------------

"""
Endpoint: POST /seed/users
คำอธิบาย:
- Endpoint ช่วยสร้างผู้ใช้ตัวอย่าง (parent/child) เพื่อทดสอบ API ได้เร็วขึ้น
- ใช้เฉพาะใน environment การพัฒนาเท่านั้น (ไม่ควรเปิดใน production)
"""
class SeedUserIn(BaseModel):
    name: str
    role: str
    email: Optional[str] = None

@app.post("/seed/users")
def seed_user(u: SeedUserIn, db: Session = Depends(get_db)):
    # ตรวจสอบ role
    if u.role not in ("parent", "child"):
        raise HTTPException(status_code=400, detail="role must be 'parent' or 'child'")
    user = User(name=u.name, role=UserRole(u.role), email=u.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "role": user.role.value}

# -----------------------
# Run instructions comment
# -----------------------

"""
สรุปการรัน:
1. ตั้งค่า DATABASE_URL เป็นของคุณ (เช่น export DATABASE_URL=...)
2. สร้าง virtualenv และติดตั้ง dependencies ตามที่กำหนด
3. รันเซิร์ฟเวอร์ด้วยคำสั่ง:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
4. ทดสอบ endpoints ผ่าน curl / Postman หรือหน้า docs ที่:
   http://localhost:8000/docs
"""
