# ส่วนนี้ของโปรแกรมทำหน้าที่เป็นจุดเริ่มต้นหลักของแอปพลิเคชัน FastAPI 
# โดยจะประกอบไปด้วยการตั้งค่าการเชื่อมต่อฐานข้อมูล การประกาศโมเดลสำหรับเก็บข้อมูล 
# รวมถึงการสร้าง endpoint ที่เกี่ยวข้องกับระบบแจ้งเตือน (Notification) 
# ซึ่งจะถูกเรียกใช้งานเมื่อ Parent อนุมัติหรือปฏิเสธงานของ Child 
# ทั้งหมดนี้ถูกเขียนรวมไว้ในไฟล์ main.py ตามที่กำหนด

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import enum

# -----------------------------------------------------------
# ส่วนนี้ของโค้ดใช้สำหรับตั้งค่าการเชื่อมต่อกับฐานข้อมูล PostgreSQL 
# โดยใช้ SQLAlchemy ORM ในการสร้าง engine และ SessionLocal 
# เพื่อให้สามารถสื่อสารกับฐานข้อมูลได้สะดวก 
# การตั้งค่านี้เป็นพื้นฐานสำคัญที่ทำให้โมเดล ORM สามารถบันทึก 
# และดึงข้อมูลจริงจาก PostgreSQL ได้
# -----------------------------------------------------------

DATABASE_URL = "postgresql+psycopg2://username:password@localhost:5432/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# -----------------------------------------------------------
# ส่วนนี้ประกาศ Enum ที่ชื่อ TaskStatus เพื่อกำหนดสถานะของงานที่เด็กส่งมา 
# โดยมีค่าได้แก่ pending (รอการตรวจสอบ), approved (อนุมัติแล้ว), rejected (ปฏิเสธแล้ว) 
# การใช้ Enum ทำให้ข้อมูลสถานะงานมีความชัดเจนและป้องกันการป้อนค่าที่ไม่ถูกต้อง
# -----------------------------------------------------------

class TaskStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# -----------------------------------------------------------
# ส่วนนี้ของโค้ดประกาศโมเดล Task และ Notification 
# โดย Task ใช้เก็บข้อมูลงานที่ Parent มอบหมายให้ Child 
# ส่วน Notification ใช้เก็บข้อความแจ้งเตือนที่ส่งไปยัง Child 
# โมเดลทั้งสองเชื่อมโยงกันด้วย ForeignKey โดย Notification จะอ้างถึง Task 
# เพื่อให้สามารถทราบว่าแจ้งเตือนนั้นเกี่ยวข้องกับงานใด
# -----------------------------------------------------------

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    child_id = Column(Integer, nullable=False)  # อ้างถึง user_id ของเด็ก
    status = Column(Enum(TaskStatus), default=TaskStatus.pending)

    notifications = relationship("Notification", back_populates="task")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    child_id = Column(Integer, nullable=False)
    message = Column(String, nullable=False)

    task = relationship("Task", back_populates="notifications")


# -----------------------------------------------------------
# ส่วนนี้สร้างตารางทั้งหมดในฐานข้อมูลตามโมเดลที่ประกาศไว้ 
# โดยใช้ Base.metadata.create_all(bind=engine) 
# ซึ่งจะทำให้ฐานข้อมูล PostgreSQL มีตาราง tasks และ notifications 
# ที่สามารถใช้งานได้ทันทีเมื่อรันโปรแกรมครั้งแรก
# -----------------------------------------------------------

Base.metadata.create_all(bind=engine)


# -----------------------------------------------------------
# ส่วนนี้สร้าง FastAPI instance ซึ่งเป็นหัวใจหลักของระบบ 
# โดย instance นี้จะทำหน้าที่รับ request จากผู้ใช้งานและส่ง response กลับ 
# API endpoints ที่จะสร้างขึ้นทั้งหมดจะผูกติดกับ instance นี้
# -----------------------------------------------------------

app = FastAPI()


# -----------------------------------------------------------
# ส่วนนี้ประกาศ dependency get_db เพื่อจัดการ session ของฐานข้อมูล 
# โดยฟังก์ชันนี้จะสร้าง session ใหม่ทุกครั้งที่มีการ request เข้ามา 
# และปิด session หลังจากใช้งานเสร็จ ช่วยให้การทำงานกับฐานข้อมูลมีความปลอดภัยและมีประสิทธิภาพ
# -----------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------
# Endpoint: อนุมัติหรือปฏิเสธงาน
# Endpoint นี้ใช้เมื่อ Parent ต้องการเปลี่ยนสถานะงานที่เด็กส่งมา 
# โดยสามารถเลือกได้ว่าจะอนุมัติหรือปฏิเสธ เมื่อสถานะถูกอัปเดต 
# ระบบจะสร้าง Notification ใหม่เพื่อแจ้งไปยัง Child โดยบันทึกข้อความแจ้งเตือนลงฐานข้อมูล
# -----------------------------------------------------------

@app.post("/tasks/{task_id}/review")
def review_task(task_id: int, action: str, db: Session = Depends(get_db)):
    # ค้นหางานตาม task_id
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # ตรวจสอบ action และเปลี่ยนสถานะงาน
    if action == "approve":
        task.status = TaskStatus.approved
        message = f"งาน '{task.title}' ได้รับการอนุมัติแล้ว"
    elif action == "reject":
        task.status = TaskStatus.rejected
        message = f"งาน '{task.title}' ถูกปฏิเสธ"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    # สร้าง Notification ใหม่สำหรับ Child
    notification = Notification(task_id=task.id, child_id=task.child_id, message=message)
    db.add(notification)
    db.commit()
    db.refresh(task)

    return {"message": "Task reviewed successfully", "task_status": task.status}


# -----------------------------------------------------------
# Endpoint: ดึงรายการแจ้งเตือนของเด็ก
# Endpoint นี้ใช้เมื่อ Child ต้องการตรวจสอบว่ามีการแจ้งเตือนอะไรบ้าง 
# โดยระบบจะดึงข้อมูลจากตาราง notifications ตาม child_id ที่ระบุ 
# และส่งกลับมาเป็นรายการข้อความทั้งหมด
# -----------------------------------------------------------

@app.get("/notifications/{child_id}")
def get_notifications(child_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.child_id == child_id).all()
    return {"child_id": child_id, "notifications": [n.message for n in notifications]}
