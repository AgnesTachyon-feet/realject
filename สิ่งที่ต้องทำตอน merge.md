# ✅ Checklist หลัง Merge ทุก Feature

เมื่อรวม branch ทั้งหมด (Tasks, Submissions, Notifications, Points) เข้าด้วยกันแล้ว ให้ตรวจสอบดังนี้:  

---

## 🔹 1. `main.py`  
- [ ] รวม router ของทุก feature ให้ครบ เช่น  
  ```python
  from app.routes import task_routes, submission_routes, notification_routes, points_routes

  app.include_router(task_routes.router)
  app.include_router(submission_routes.router)
  app.include_router(notification_routes.router)
  app.include_router(points_routes.router)
🔹 2. Models (app/models/)
 ตรวจสอบว่าแต่ละโมเดล (Task, Submission, Notification, PointsHistory) ไม่ซ้ำซ้อน

 ความสัมพันธ์ (relationship) เชื่อมครบ เช่น Task.submissions ↔ Submission.task

 ForeignKey อ้างอิงตารางถูกต้อง

🔹 3. Schemas (app/schemas/)
 Schema ของแต่ละ feature ไม่มีชื่อซ้ำ

 Response model ที่ใช้ข้าม feature (เช่น TaskOut) import จากไฟล์เดียวกัน

 ไม่มี import loop ระหว่าง schemas

🔹 4. Routes (app/routes/)
 ทุก router มี prefix ชัดเจน ไม่ชนกัน

/tasks

/submissions

/notifications

/points

 response_model ของแต่ละ endpoint ถูกต้อง

🔹 5. Upload Files (Submission)
 มีการสร้างโฟลเดอร์ uploads/ ก่อนใช้งาน

python
Copy code
os.makedirs("uploads", exist_ok=True)
🔹 6. Database Migration
 Base.metadata.create_all(bind=engine) ครอบคลุม model ทั้งหมด

 ถ้าใช้ Alembic → generate migration ใหม่หลัง merge

🔹 7. Integration Test (Flow ครบวงจร)
 Parent → สร้างภารกิจ

 Child → เห็นภารกิจ

 Child → ส่งงาน

 Parent → อนุมัติ/ปฏิเสธงาน

 Child → แต้มเปลี่ยน + มี notification

