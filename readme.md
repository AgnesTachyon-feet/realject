# อ่านก่อนใช้

### ถ้าต้องพิมพ์ command อะไรก็ตาม ต้อง terminal 
ซึ่งมันที่อยู่ tap ด้านบนซ้ายของจอ หรือกด `Ctrl+Shift+ปุ่มเปลี่ยนภาษา` (คีย์ลัดนี้จะใช้ได้ก็ต่อเมื่อปุ่ม ` ไม่ได้ทำหน้าที่เป็นปุ่มเปลี่ยนภาษา) ตัวเลือกที่จะใช้บ่อยจะมี cmd, bash
## ต้อง install python 3.1x, PostgresSQL
### มาถึง ก็พิมพ์
`py -m venv venv`
`venv\Scripts\activate.bat`
`pip install -r requirements.txt`
เพื่อ install library python

### fastapi ใช้ยิง api สื่อสารกันระหว่าง front-end กับ back-end 
เวลาจะใช้ให้พิมพ์ว่า (ก่อนใช้ก็เปิด venv ก่อน) `uvicorn main:app --reload`
พอพิมพ์เสร็จมันจะมีลิงค์ให้คลิ๊ก ให้กด `Ctrl+clickซ้าย`

`ถ้าจะทำ feature ใหม่ก็เปิด git bash` แล้วพิมพ์
`git checkout -b feature/ชื่อฟีเจอร์ตั้งให้มีความหมาย`
