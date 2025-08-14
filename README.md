🚀 เทคโนโลยีที่ใช้
โปรเจกต์นี้พัฒนาขึ้นบนเทคโนโลยีหลักดังต่อไปนี้:

Backend: Python 3.x, Django 4.x

Database: SQLite (สำหรับ Local Development), PostgreSQL/MySQL (สำหรับ Production)

Dependency Management: Pip

Frontend: HTML5, CSS3, JavaScript

Other: Git

🛠️ การติดตั้งและรันโปรเจกต์
1. การโคลน Repository
เปิด Terminal หรือ Command Prompt ขึ้นมา จากนั้นใช้คำสั่ง git clone เพื่อดาวน์โหลดโค้ดโปรเจกต์จาก GitHub:



git clone https://github.com/Teeraphat2543Inta/Kathai.git

2. เข้าสู่ไดเรกทอรีโปรเจกต์
ใช้คำสั่ง cd เพื่อย้ายเข้าไปในโฟลเดอร์ของโปรเจกต์:


cd Kathai

3. สร้างและเปิดใช้งาน Virtual Environment
เพื่อแยกแพ็กเกจของโปรเจกต์นี้ออกจากแพ็กเกจอื่นๆ ในเครื่องของคุณ:


python -m venv venv

บน Windows:


venv\Scripts\activate

บน macOS และ Linux:

source venv/bin/activate

4. ติดตั้งแพ็กเกจที่จำเป็น
ติดตั้งแพ็กเกจ Python ทั้งหมดที่ระบุในไฟล์ requirements.txt:

Bash

pip install -r requirements.txt

5. ตั้งค่าฐานข้อมูล
รันคำสั่ง migrate เพื่อสร้างตารางฐานข้อมูลตาม Models ที่กำหนดไว้ใน Django:

Bash

python manage.py makemigrations
python manage.py migrate
6. สร้างบัญชีผู้ดูแลระบบ (Superuser)
หากต้องการเข้าถึงหน้า Admin Panel ของ Django ให้สร้างบัญชีผู้ดูแลระบบ:

Bash

python manage.py createsuperuser
7. รันเซิร์ฟเวอร์
เริ่มการทำงานของเซิร์ฟเวอร์พัฒนา:

Bash

python manage.py runserver
ตอนนี้โปรเจกต์จะเปิดให้บริการที่ http://127.0.0.1:8000/

การเตรียมโค้ดและการอัปโหลดขึ้น GitHub
เมื่อคุณมีการแก้ไขโค้ดและต้องการส่งขึ้นไปบน GitHub ให้ทำตามขั้นตอนเหล่านี้:

1. เตรียมไฟล์ requirements.txt (หากมีการติดตั้งแพ็กเกจใหม่)
หากคุณติดตั้งแพ็กเกจใหม่ในโปรเจกต์ อย่าลืมอัปเดตไฟล์ requirements.txt ด้วยคำสั่ง:

Bash

pip freeze > requirements.txt
2. เพิ่มไฟล์และบันทึกการเปลี่ยนแปลง (Commit)
ใช้คำสั่ง git add . เพื่อเพิ่มไฟล์ทั้งหมดที่คุณแก้ไขหรือสร้างขึ้น จากนั้นใช้ git commit เพื่อบันทึกการเปลี่ยนแปลงนั้นๆ

Bash

git add .
git commit -m "อธิบายการเปลี่ยนแปลงของคุณที่นี่"
3. อัปโหลดโค้ดขึ้น GitHub (Push)
ใช้คำสั่ง git push เพื่อส่งโค้ดขึ้นไปที่ repository บน GitHub ของคุณ

Bash

git push origin main
หากเป็นการ push ครั้งแรกของโปรเจกต์ ให้ใช้คำสั่งเต็มดังนี้ เพื่อกำหนด upstream branch:

Bash

git push -u origin main
