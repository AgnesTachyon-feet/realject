# ส่วนนี้ของโปรแกรมนำเข้าโมดูลและไลบรารีที่จำเป็นสำหรับการทำงานของแอปพลิเคชัน
# โดยเราจะใช้ FastAPI เป็น framework หลักในการสร้าง REST API
# และใช้ SQLAlchemy ORM ในการจัดการฐานข้อมูล PostgreSQL
# รวมถึงการใช้ sessionmaker สำหรับสร้าง session เพื่อเชื่อมต่อกับฐานข้อมูล
# ไลบรารีเหล่านี้ถือเป็นหัวใจสำคัญที่ทำให้แอปสามารถทำงานร่วมกับฐานข้อมูลได้อย่างราบรื่น
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
import datetime

# -------------------------------------------------------
# ส่วนนี้ของโปรแกรมทำหน้าที่กำหนดการเชื่อมต่อกับฐานข้อมูล PostgreSQL
# โดยกำหนด URL สำหรับการเชื่อมต่อไปยังฐานข้อมูล เช่น user, password, host, port, และชื่อ database
# เมื่อสร้าง engine ขึ้นมาแล้ว เราจะใช้ engine นี้ร่วมกับ SQLAlchemy ORM
# เพื่อจัดการคำสั่ง SQL ในรูปแบบ object-oriented โดยไม่ต้องเขียน SQL ดิบเอง
# นอกจากนี้ยังสร้าง SessionLocal สำหรับสร้าง session เชื่อมต่อกับฐานข้อมูล
# และ Base สำหรับใช้เป็นแม่แบบของ ORM model ทั้งหมด
# -------------------------------------------------------
DATABASE_URL = "postgresql://user:password@localhost:5432/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------------------------------------
# ส่วนนี้ของโปรแกรมสร้าง Dependency ฟังก์ชัน get_db
# เพื่อให้ endpoint สามารถใช้ session ในการเชื่อมต่อกับฐานข้อมูลได้อย่างสะดวก
# โดยจะเปิด session เมื่อมีการเรียกใช้งาน และปิด session เมื่อทำงานเสร็จสิ้น
# เพื่อป้องกัน resource leak ที่อาจเกิดขึ้นหาก session ไม่ถูกปิด
# -------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------
# ส่วนนี้เป็นการสร้าง ORM Model สำหรับ Reward
# Reward คือของรางวัลที่ผู้ปกครองสร้างขึ้น และเด็กสามารถใช้แต้มสะสมมาแลกได้
# ตารางนี้เก็บข้อมูล เช่น ชื่อของรางวัล คำอธิบาย แต้มที่ต้องใช้ และจำนวนคงเหลือ
# โมเดลนี้เชื่อมโยงกับ RewardRedemption เพื่อให้รู้ว่ามีการแลกของรางวัลใดไปแล้วบ้าง
# -------------------------------------------------------
class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    cost = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)

    redemptions = relationship("RewardRedemption", back_populates="reward")

# -------------------------------------------------------
# ส่วนนี้เป็นการสร้าง ORM Model สำหรับ RewardRedemption
# RewardRedemption ใช้เก็บข้อมูลการแลกของรางวัลของเด็ก
# เช่น เด็กคนไหนแลกรางวัลอะไร และสถานะของการแลก (pending หรือ confirmed)
# เมื่อการแลกสำเร็จ จะถูกบันทึกว่า confirmed และสามารถใช้เพื่อแจ้งเตือนเด็กได้
# -------------------------------------------------------
class RewardRedemption(Base):
    __tablename__ = "reward_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, nullable=False)
    reward_id = Column(Integer, ForeignKey("rewards.id"))
    status = Column(String, default="pending")  # pending, confirmed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reward = relationship("Reward", back_populates="redemptions")

# -------------------------------------------------------
# ส่วนนี้เป็นการสร้าง ORM Model สำหรับ Notification
# Notification ใช้เก็บข้อความแจ้งเตือนที่ส่งถึงผู้ใช้งาน
# เช่น เมื่อเด็กแลกของรางวัลสำเร็จ จะมีการสร้าง notification เพื่อแจ้งเด็กคนนั้น
# ข้อมูลที่เก็บ เช่น ข้อความแจ้งเตือน เวลาที่สร้าง และสถานะว่าอ่านข้อความแล้วหรือยัง
# -------------------------------------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # สมมติว่า user_id คือ child_id
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# -------------------------------------------------------
# ส่วนนี้ของโปรแกรมจะสร้างตารางทั้งหมดในฐานข้อมูลตามโมเดลที่เราได้กำหนดไว้ด้านบน
# โดยใช้ Base.metadata.create_all(bind=engine)
# ฟังก์ชันนี้จะตรวจสอบว่ามีตารางเหล่านี้ในฐานข้อมูลหรือยัง
# หากยังไม่มี ระบบจะทำการสร้างขึ้นมาใหม่โดยอัตโนมัติ
# -------------------------------------------------------
Base.metadata.create_all(bind=engine)

# -------------------------------------------------------
# ส่วนนี้เป็นการสร้าง FastAPI instance
# ซึ่งเป็นหัวใจหลักของแอปพลิเคชัน โดย instance นี้จะคอยรับ request
# และส่ง response กลับไปยังผู้ใช้งานตามเส้นทาง (endpoint) ที่เรากำหนด
# -------------------------------------------------------
app = FastAPI(title="Reward Notification System")

# -------------------------------------------------------
# Endpoint นี้ทำหน้าที่เป็น root ของระบบ
# เมื่อผู้ใช้เข้ามาที่ path “/” จะได้รับข้อความต้อนรับกลับไป
# จุดประสงค์หลักเพื่อให้ตรวจสอบว่า API ทำงานอยู่หรือไม่
# -------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Reward Notification API is running"}

# -------------------------------------------------------
# Endpoint นี้ใช้สำหรับยืนยันการแลกของรางวัล (reward redemption)
# เมื่อเด็กแลกรางวัลและผู้ปกครองยืนยันการแลกสำเร็จ
# ระบบจะอัปเดตสถานะของการแลกเป็น confirmed
# และสร้าง notification ใหม่ให้กับเด็กเพื่อแจ้งว่าแลกของรางวัลสำเร็จแล้ว
# -------------------------------------------------------
@app.post("/redeem/{redemption_id}/confirm")
def confirm_reward_redemption(redemption_id: int, db: Session = Depends(get_db)):
    redemption = db.query(RewardRedemption).filter(RewardRedemption.id == redemption_id).first()
    if not redemption:
        raise HTTPException(status_code=404, detail="Redemption not found")

    redemption.status = "confirmed"
    db.add(redemption)

    # สร้างข้อความแจ้งเตือนเมื่อแลกของรางวัลสำเร็จ
    notification = Notification(
        user_id=redemption.child_id,
        message=f"🎉 การแลกของรางวัล {redemption.reward.title} สำเร็จแล้ว!",
        is_read=False
    )
    db.add(notification)
    db.commit()
    db.refresh(redemption)
    db.refresh(notification)

    return {"message": "Reward redemption confirmed and notification sent."}

# -------------------------------------------------------
# Endpoint นี้ใช้สำหรับดึงรายการ notification ของผู้ใช้ (เด็ก)
# โดยระบุ user_id เพื่อให้ระบบค้นหาข้อความแจ้งเตือนทั้งหมดที่เกี่ยวข้องกับเด็กคนนั้น
# ผลลัพธ์ที่ได้คือรายการข้อความที่สามารถนำไปแสดงในแอปของเด็กได้
# -------------------------------------------------------
@app.get("/notifications/{user_id}")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
    return {"notifications": [{"id": n.id, "message": n.message, "is_read": n.is_read, "created_at": n.created_at} for n in notifications]}
