# prompt ให้ใช้เวลาให้ AI gen code
เขียนโค้ดภาษา Python โดยใช้ FastAPI และ SQLAlchemy ORM สำหรับ [งานที่ต้องการ]  
โดยมีเงื่อนไขดังนี้:

1. โค้ดหลักเขียนอยู่ในไฟล์ main.py และทำงานบน virtual environment (venv)  
   ซึ่งติดตั้ง library ไว้แล้วดังนี้:
   annotated-types==0.7.0
   anyio==4.10.0
   bcrypt==4.0.1
   click==8.2.1
   colorama==0.4.6
   ecdsa==0.19.1
   fastapi==0.116.1
   greenlet==3.2.4
   h11==0.16.0
   idna==3.10
   passlib==1.7.4
   psycopg2-binary==2.9.10
   pyasn1==0.6.1
   pydantic==2.11.7
   pydantic_core==2.33.2
   PyJWT==2.10.1
   python-jose==3.5.0
   rsa==4.9.1
   six==1.17.0
   sniffio==1.3.1
   SQLAlchemy==2.0.43
   starlette==0.47.3
   typing-inspection==0.4.1
   typing_extensions==4.15.0
   uvicorn==0.35.0

2. ใช้กฎการตั้งชื่อ:
   - ตัวแปร: snake_case เช่น user_name, total_score
   - ฟังก์ชัน: snake_case เช่น calculate_score, save_data
   - คลาส: PascalCase เช่น UserData, FileManager

3. ต้องใช้ **PostgreSQL** เป็นฐานข้อมูล  
   - ใช้ SQLAlchemy ORM เชื่อมต่อและจัดการข้อมูล  
   - กำหนด engine, session, และ Base สำหรับ ORM  
   - สร้างโมเดล ORM และใช้ในการบันทึก/ดึงข้อมูลจาก PostgreSQL  

4. เพิ่มคอมเมนต์ก่อนแต่ละส่วนของโค้ด โดยคอมเมนต์ต้องเป็น
   - คำอธิบายยาวๆ แบบย่อหน้า (2–5 บรรทัด)  
   - อธิบายว่าโค้ดส่วนนั้นทำงานอะไร ทำไมต้องมี และเกี่ยวข้องกับตัวแปรหรือฟังก์ชันใด  
   - เขียนให้อ่านเข้าใจง่าย เหมือนเขียนรายงานอธิบายโค้ด

5. ห้ามใช้คอมเมนต์สั้นๆ เช่น “# รับค่าจากผู้ใช้”  
   ต้องเขียนยาวเหมือนรายงาน เช่น:  
   ` ส่วนนี้ของโปรแกรมสร้าง FastAPI instance ซึ่งเป็นหัวใจหลักของแอปพลิเคชัน  `
   ` โดย instance นี้จะทำหน้าที่รับ request และส่ง response กลับไปยังผู้ใช้งาน  `

6. เขียนโค้ดให้สามารถรันได้จริง โดยใช้ FastAPI ทำงานเป็น REST API

7. ทุก endpoint ต้องมีคอมเมนต์อธิบายว่า endpoint นั้นใช้ทำอะไร  
   เช่น การรับข้อมูล, การบันทึก, การดึงข้อมูล ฯลฯ