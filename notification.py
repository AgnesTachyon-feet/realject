# main.py

"""
ส่วนนี้ของโปรแกรมทำหน้าที่เป็นจุดเริ่มต้น (Entry Point) ของระบบ FastAPI
ซึ่งประกอบด้วยการเชื่อมต่อฐานข้อมูล การสร้างตาราง ORM การสร้าง FastAPI instance
และการประกาศ endpoint ที่ใช้ติดต่อกับ client โดย endpoint จะช่วยให้เราสามารถ
จัดการข้อมูลการแจ้งเตือน (Notifications) ได้ เช่น การสร้าง การดึงข้อมูล และการลบ
ทั้งหมดนี้ทำให้ API สามารถทำงานแบบ RESTful และรองรับการทำงานกับฐานข้อมูล PostgreSQL
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime
import os

# ---------------------------------------------------------------------------------
# ส่วนนี้ของโปรแกรมกำหนดการเชื่อมต่อกับฐานข้อมูล PostgreSQL โดยใช้ SQLAlchemy ORM
# โดยใช้ environment variable "DATABASE_URL" หากไม่ถูกตั้งค่า จะใช้ค่าเริ่มต้น
# ซึ่งประกอบไปด้วย username, password, host, port, และชื่อ database
# การใช้ engine และ sessionmaker ทำให้สามารถสร้าง session เพื่อติดต่อกับฐานข้อมูล
# ได้อย่างเป็นระบบและปลอดภัย
# ---------------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/mydb"  # ค่า default
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------------
# ส่วนนี้ของโปรแกรมสร้างโมเดล ORM ที่ชื่อว่า Notification
# โดยจะเป็นตัวแทนของตาราง "notifications" ในฐานข้อมูล
# ตารางนี้ใช้เก็บข้อมูลเกี่ยวกับการแจ้งเตือน เช่น ข้อความการแจ้งเตือน
# สถานะการอ่านแล้วหรือยัง และวันที่สร้าง เพื่อใช้ในการแจ้งเตือนผู้ใช้งาน
# ---------------------------------------------------------------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # ระบุว่าเป็นการแจ้งเตือนของ user คนไหน
    message = Column(String, nullable=False)   # ข้อความการแจ้งเตือน
    is_read = Column(Boolean, default=False)   # ระบุว่าอ่านแล้วหรือยัง
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # วันที่สร้าง


# ---------------------------------------------------------------------------------
# ส่วนนี้ของโปรแกรมใช้เพื่อสร้างตารางทั้งหมดที่ถูกประกาศไว้ใน ORM models
# โดยใช้ Base.metadata.create_all(bind=engine) ซึ่งจะตรวจสอบและสร้างตารางใหม่
# หากยังไม่มีในฐานข้อมูล เพื่อให้มั่นใจว่าฐานข้อมูลพร้อมใช้งานเมื่อ API ถูกเรียกใช้
# ---------------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------------
# ส่วนนี้ของโปรแกรมสร้าง FastAPI instance ซึ่งเป็นหัวใจหลักของแอปพลิเคชัน
# โดย instance นี้จะทำหน้าที่รับ request และส่ง response กลับไปยังผู้ใช้งาน
# เราจะประกาศ endpoint ต่าง ๆ ไว้ภายใต้ instance นี้
# ---------------------------------------------------------------------------------
app = FastAPI(title="Notification API with FastAPI & PostgreSQL")


# ---------------------------------------------------------------------------------
# ส่วนนี้ของโปรแกรมสร้าง dependency สำหรับ Session
# เพื่อให้ endpoint สามารถเชื่อมต่อฐานข้อมูลได้สะดวก โดยเมื่อเรียกใช้
# ฟังก์ชัน get_db() จะสร้าง session ใหม่ และเมื่อทำงานเสร็จแล้วจะปิดการเชื่อมต่อ
# เพื่อป้องกันปัญหาการเชื่อมต่อค้างในระบบ
# ---------------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------------
# Endpoint: GET /
# Endpoint นี้ใช้สำหรับตรวจสอบว่า API ทำงานอยู่หรือไม่
# โดยจะส่งข้อความต้อนรับกลับไปยัง client
# ---------------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Notification API is running"}


# ---------------------------------------------------------------------------------
# Endpoint: POST /notifications/
# Endpoint นี้ใช้สำหรับสร้างการแจ้งเตือนใหม่ โดยรับค่า user_id และ message
# แล้วบันทึกลงในฐานข้อมูล โดยกำหนดค่าเริ่มต้น is_read = False
# และบันทึกเวลา created_at เป็นเวลาปัจจุบัน เมื่อบันทึกสำเร็จจะคืนค่ารายละเอียด
# ของการแจ้งเตือนที่สร้างใหม่กลับไปยัง client
# ---------------------------------------------------------------------------------
@app.post("/notifications/")
def create_notification(user_id: int, message: str, db: Session = Depends(get_db)):
    new_notification = Notification(user_id=user_id, message=message)
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return {
        "id": new_notification.id,
        "user_id": new_notification.user_id,
        "message": new_notification.message,
        "is_read": new_notification.is_read,
        "created_at": new_notification.created_at,
    }


# ---------------------------------------------------------------------------------
# Endpoint: GET /notifications/{user_id}
# Endpoint นี้ใช้สำหรับดึงรายการการแจ้งเตือนทั้งหมดของผู้ใช้ตาม user_id
# โดยจะค้นหาจากตาราง notifications และส่งกลับมาเป็นรายการ
# ถ้าไม่พบข้อมูล จะส่งกลับเป็น list ว่าง เพื่อให้ client นำไปแสดงผลได้
# ---------------------------------------------------------------------------------
@app.get("/notifications/{user_id}")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
    return notifications


# ---------------------------------------------------------------------------------
# Endpoint: DELETE /notifications/{notification_id}
# Endpoint นี้ใช้สำหรับลบการแจ้งเตือนออกจากฐานข้อมูลตาม id ที่ระบุ
# โดยหากไม่พบข้อมูลจะส่ง error 404 กลับไป หากพบข้อมูลจะลบและยืนยันการทำงาน
# ด้วยการส่งข้อความ "Notification deleted successfully"
# ---------------------------------------------------------------------------------
@app.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted successfully"}


