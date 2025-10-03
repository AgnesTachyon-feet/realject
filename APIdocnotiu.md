ตัวอย่างการใช้งาน Notification API ที่คุณจะได้หลังจากเพิ่ม notification.py ทั้งหมดเข้าโปรเจกต์

1) ดึงรายการ Notification ของผู้ใช้
Request
GET /notifications/2

Response (JSON)
[
  {
    "id": 5,
    "message": "เด็กส่งงาน: ทำการบ้านวิทย์",
    "is_read": false,
    "created_at": "2025-09-25T12:30:00"
  },
  {
    "id": 3,
    "message": "งาน ทำการบ้านคณิต ได้รับการอนุมัติ +10       แต้ม",
    "is_read": true,
    "created_at": "2025-09-24T15:45:00"
  }
]


🔎 คำอธิบาย

id → รหัสแจ้งเตือน

message → ข้อความแจ้งเตือน

is_read → สถานะอ่านแล้วหรือยัง

created_at → วันที่เวลาที่สร้าง

2) เปลี่ยนสถานะแจ้งเตือนเป็น "อ่านแล้ว"
Request
PATCH /notifications/5/read

Response
{
  "id": 5,
  "message": "เด็กส่งงาน: ทำการบ้านวิทย์",
  "is_read": true,
  "created_at": "2025-09-25T12:30:00"
}


🔎 คำอธิบาย

แจ้งเตือนที่ id=5 ถูกอัปเดตเป็น อ่านแล้ว (is_read: true)

3) การทำงานรวมกับระบบ Submission

เวลาเด็กส่งงาน (POST /submissions/) → ระบบสามารถสร้าง Notification ให้ parent ได้ เช่น:

{
  "id": 6,
  "message": "เด็กส่งงาน: โครงงานประวัติศาสตร์",
  "is_read": false,
  "created_at": "2025-09-25T17:00:00"
}


เวลา parent อนุมัติงาน (PATCH /submissions/{id}/decision) → เด็กก็จะได้รับ Notification เช่น:

{
  "id": 7,
  "message": "งาน โครงงานประวัติศาสตร์ ได้รับการอนุมัติ +15 แต้ม",
  "is_read": false,
  "created_at": "2025-09-25T17:05:00"
}


✅ แบบนี้คุณจะได้ flow การแจ้งเตือนครบทั้ง ดู → อ่าน → ผูกกับงานที่เกิดขึ้นในระบบ

อยากให้ผมทำ ไฟล์ API Documentation (.md) สำหรับ Notification โดยเฉพาะ (พร้อม request/response ตัวอย่างแบบ Postman) ไว้ให้เลยไหมครับ?

You said:
เอา
ChatGPT said:

โอเคครับ 🙌 ผมจะทำไฟล์ Markdown สำหรับ API Documentation ของ Notification ให้เลย
คุณสามารถวางไฟล์นี้ในโปรเจกต์เป็น NOTIFICATION_API.md แล้วใช้กับทีมได้ทันที

# 📩 Notification API Documentation

ระบบ Notification ใช้สำหรับแจ้งเตือนเหตุการณ์ต่าง ๆ ภายในแอป เช่น เด็กส่งงาน, ผู้ปกครองอนุมัติ/ปฏิเสธงาน, หรือแต้มสะสม

---

## 🔹 Base URL


/notifications


---

## 1) ดึงรายการ Notification ของผู้ใช้

### Endpoint


GET /notifications/{user_id}


### Parameters
- `user_id` (int, path) → รหัสผู้ใช้ที่ต้องการดูแจ้งเตือน

### Response
```json
[
  {
    "id": 5,
    "message": "เด็กส่งงาน: ทำการบ้านวิทย์",
    "is_read": false,
    "created_at": "2025-09-25T12:30:00"
  },
  {
    "id": 3,
    "message": "งาน ทำการบ้านคณิต ได้รับการอนุมัติ +10 แต้ม",
    "is_read": true,
    "created_at": "2025-09-24T15:45:00"
  }
]

2) เปลี่ยนสถานะแจ้งเตือนเป็น "อ่านแล้ว"
Endpoint
PATCH /notifications/{notification_id}/read

Parameters

notification_id (int, path) → รหัสของ Notification ที่ต้องการเปลี่ยนสถานะ

Response
{
  "id": 5,
  "message": "เด็กส่งงาน: ทำการบ้านวิทย์",
  "is_read": true,
  "created_at": "2025-09-25T12:30:00"
}

3) การทำงานร่วมกับระบบอื่น
🔸 เมื่อเด็กส่งงาน (POST /submissions/)

ระบบจะสร้าง Notification ให้ parent:

{
  "id": 6,
  "message": "เด็กส่งงาน: โครงงานประวัติศาสตร์",
  "is_read": false,
  "created_at": "2025-09-25T17:00:00"
}

🔸 เมื่อ parent อนุมัติ/ปฏิเสธงาน (PATCH /submissions/{id}/decision)

ระบบจะสร้าง Notification ให้ child:

{
  "id": 7,
  "message": "งาน โครงงานประวัติศาสตร์ ได้รับการอนุมัติ +15 แต้ม",
  "is_read": false,
  "created_at": "2025-09-25T17:05:00"
}

🛠 Notes

is_read = false → ยังไม่ได้เปิดดู

is_read = true → อ่านแล้ว

การ query Notification ควรเรียงตาม created_at DESC เพื่อให้เห็นรายการล่าสุดก่อน