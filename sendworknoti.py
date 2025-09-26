# main.py

# ส่วนนี้ทำหน้าที่นำเข้าโมดูลและไลบรารีที่จำเป็นต่อการทำงานของแอปพลิเคชัน
# ไลบรารีที่ใช้ ได้แก่ FastAPI สำหรับสร้าง REST API, SQLAlchemy สำหรับเชื่อมต่อและจัดการฐานข้อมูล
# รวมถึง sessionmaker และ declarative_base ที่ใช้สร้าง ORM model และ session เพื่อเชื่อมโยงกับ PostgreSQL
# การนำเข้าเหล่านี้มีความสำคัญเพราะเป็นพื้นฐานที่ทำให้ระบบสามารถสร้าง API และทำงานร่วมกับฐานข้อมูลได้อย่างเป็นระบบ
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from pydantic import BaseModel
import datetime


# ส่วนนี้ของโปรแกรมทำหน้าที่สร้างการเชื่อมต่อกับฐานข้อมูล PostgreSQL
# โดยใช้ SQLAlchemy engine ซึ่งจะต้องใส่ connection string ที่บอกว่าใช้ driver อะไร
# และเชื่อมไปยัง host, port, username, password, และชื่อฐานข้อมูลใด
# การกำหนด engine ตรงนี้เป็นหัวใจในการเชื่อมโยง ORM เข้ากับ PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost:5432/child_mission_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ส่วนนี้ของโค้ดเป็นการกำหนด ORM Models ซึ่งใช้ในการสร้างตารางในฐานข้อมูล
# มีการสร้าง 3 ตารางหลัก คือ User, Task และ Notification
# - User: เก็บข้อมูลผู้ใช้ทั้ง Parent และ Child
# - Task: เก็บข้อมูลภารกิจที่ Parent มอบหมายให้ Child
# - Notification: เก็บข้อความแจ้งเตือนเมื่อ Child ส่งงาน เพื่อให้ Parent ตรวจสอบ
# การใช้ ORM ช่วยให้เขียนโค้ด Python แทน SQL ได้ ทำให้อ่านง่ายและบำรุงรักษาสะดวก
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)  # parent หรือ child

    tasks = relationship("Task", back_populates="child")
    notifications = relationship("Notification", back_populates="parent")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    child_id = Column(Integer, ForeignKey("users.id"))
    parent_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, submitted, approved

    child = relationship("User", back_populates="tasks", foreign_keys=[child_id])
    parent = relationship("User", foreign_keys=[parent_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    parent = relationship("User", back_populates="notifications")


# ส่วนนี้เป็นการสร้างตารางในฐานข้อมูลตามที่เราได้กำหนดใน ORM Models
# ฟังก์ชัน Base.metadata.create_all(engine) จะตรวจสอบว่าในฐานข้อมูลมีตารางที่เราต้องการหรือยัง
# ถ้าไม่มีก็จะทำการสร้างใหม่ ซึ่งทำให้การเริ่มต้นใช้งานแอปพลิเคชันง่ายและสะดวกขึ้น
Base.metadata.create_all(bind=engine)


# ส่วนนี้สร้าง FastAPI instance ซึ่งเป็นหัวใจหลักของแอปพลิเคชัน
# instance นี้จะทำหน้าที่รับ HTTP request และส่ง response กลับไปยังผู้ใช้งาน
# การสร้าง instance ของ FastAPI ตรงนี้ทำให้เราสามารถกำหนดเส้นทาง (endpoint)
# และจัดการกับ logic ของแอปพลิเคชันในรูปแบบ REST API ได้อย่างชัดเจน
app = FastAPI()


# ส่วนนี้เป็น dependency function ที่สร้าง session เชื่อมกับฐานข้อมูล
# ทุกครั้งที่มี request เข้ามา session จะถูกสร้างขึ้นมาใหม่
# และเมื่อเสร็จสิ้นการทำงานแล้ว session จะถูกปิดเพื่อป้องกัน memory leak
# การเขียนในรูปแบบ dependency ของ FastAPI ทำให้โค้ดสะอาดและปลอดภัยยิ่งขึ้น
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ส่วนนี้กำหนด Pydantic Schemas ซึ่งเป็นตัวกลางในการตรวจสอบและ validate ข้อมูล
# - TaskSubmit: ใช้เมื่อ Child ส่งงาน โดยจะต้องบอก task_id
# - NotificationResponse: ใช้ในการส่งข้อมูลแจ้งเตือนกลับไปยังผู้ใช้งาน
# การใช้ Pydantic ช่วยให้มั่นใจว่าข้อมูลที่เข้าออก API ถูกต้องตามที่กำหนด
class TaskSubmit(BaseModel):
    task_id: int


class NotificationResponse(BaseModel):
    id: int
    message: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True


# Endpoint นี้ใช้สำหรับ Child ในการส่งงานที่ได้รับมอบหมาย
# เมื่อ Child กดส่งงาน ระบบจะเปลี่ยนสถานะ task เป็น "submitted"
# และสร้าง Notification ใหม่เพื่อแจ้งเตือน Parent ว่ามีงานที่ถูกส่งมาแล้ว
# จากนั้นจะบันทึกข้อมูลการแจ้งเตือนลงในฐานข้อมูล
@app.post("/tasks/submit")
def submit_task(submission: TaskSubmit, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == submission.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "submitted"

    notification = Notification(
        parent_id=task.parent_id,
        message=f"Child has submitted task: {task.title}"
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return {"message": "Task submitted successfully and notification sent to parent."}


# Endpoint นี้ใช้สำหรับ Parent ในการดึงรายการแจ้งเตือนทั้งหมด
# โดยระบบจะค้นหาในตาราง Notification ตาม parent_id ที่ระบุ
# และส่งข้อมูลแจ้งเตือนทั้งหมดกลับมาในรูปแบบ JSON
# สิ่งนี้ช่วยให้ Parent สามารถตรวจสอบการส่งงานของ Child ได้ง่าย
@app.get("/notifications/{parent_id}", response_model=list[NotificationResponse])
def get_notifications(parent_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.parent_id == parent_id).all()
    return notifications
