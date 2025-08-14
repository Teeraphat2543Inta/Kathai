# 🏦 Kathai — ระบบเปรียบเทียบรีไฟแนนซ์บ้าน

แพลตฟอร์มช่วยเปรียบเทียบข้อเสนอรีไฟแนนซ์จากหลายธนาคารแบบเรียลไทม์ พร้อมวิซาร์ดเก็บอินพุตผู้ใช้ คำนวณค่างวด ค่าธรรมเนียม และเงินที่ประหยัดได้ โดยดึงข้อมูลจริงจากฐานข้อมูล (ไม่ใช่ mock)

---

## 🚀 เทคโนโลยีที่ใช้

- **Backend**: Python 3.9+ · Django 4.x  
- **Database**: 
  - Local: SQLite (ค่าเริ่มต้น)
  - Production: PostgreSQL หรือ MySQL
- **Dependency**: pip / requirements.txt  
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap Icons  
- **Version Control**: Git + GitHub

> แนะนำให้ใช้ Python 3.9–3.11 เพื่อความเข้ากันได้สูงสุดกับ Django 4.2.x

---

## 🧰 เตรียมเครื่องก่อนเริ่ม (Prerequisites)

- ติดตั้ง **Git** และ **Python** (เช็คเวอร์ชันด้วย `python --version`)
- แนะนำให้ใช้ **Virtual Environment** แยกโปรเจกต์

---

## 🛠️ การติดตั้งและรันโปรเจกต์ (Local Development)

1) **โคลน repository**
```bash
git clone https://github.com/Teeraphat2543Inta/Kathai.git
cd Kathai


สร้างและเปิดใช้งาน Virtual Environment

# สร้าง venv
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

ติดตั้งแพ็กเกจที่จำเป็น

pip install --upgrade pip
pip install -r requirements.txt

ตั้งค่าฐานข้อมูลและ migrate
ค่าเริ่มต้นใช้ SQLite พร้อมใช้งานทันที

python manage.py makemigrations
python manage.py migrate

สร้าง Superuser (สำหรับเข้า /admin)

python manage.py createsuperuser

รันเซิร์ฟเวอร์

python manage.py runserver

🗄️ การตั้งค่าฐานข้อมูล (Production)
ตัวเลือก A: PostgreSQL

แก้ settings.py ให้ใช้ PostgreSQL (หรือใช้ตัวแปรแวดล้อมของคุณเอง)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "kathai",
        "USER": "postgres",
        "PASSWORD": "your-password",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

ตัวเลือก B: MySQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "kathai",
        "USER": "root",
        "PASSWORD": "your-password",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    }
}


แนะนำ: ตั้งค่า DEBUG=False, เพิ่มโดเมนจริงใน ALLOWED_HOSTS, และตั้งค่า SECRET_KEY ผ่าน Environment Variable ในโปรดักชัน

🔐 การตั้งค่า Environment (แนะนำ)

สร้างไฟล์ .env (ถ้าโปรเจกต์รองรับการอ่าน .env) แล้วกำหนดค่าหลัก ๆ เช่น

DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=127.0.0.1,localhost
# DATABASE_URL=postgres://user:pass@host:5432/kathai  # ถ้าใช้ dj-database-url


หากโปรเจกต์ยังไม่รองรับ .env สามารถกำหนดค่าผ่านตัวแปรระบบ (Environment) หรือแก้ใน settings.py ได้โดยตรง

🧪 การทดสอบ (Tests)
python manage.py test

📦 จัดการแพ็กเกจ

อัปเดตไฟล์ requirements.txt หลังติดตั้งแพ็กเกจใหม่

pip freeze > requirements.txt

⬆️ อัปโหลดโค้ดขึ้น GitHub
git add .
git commit -m "อธิบายการเปลี่ยนแปลงของคุณที่นี่"
git push origin main

# กรณี push ครั้งแรกของเครื่องนี้/รีโมตนี้
git push -u origin main

🧭 โครงสร้างโปรเจกต์ (โดยสังเขป)
Kathai/
├─ manage.py
├─ requirements.txt
├─ <project_name>/settings.py
├─ refinance/                 # แอปหลัก (views, models, forms, templates)
│  ├─ templates/refinance/
│  │  ├─ loan_comparison_results.html
│  │  ├─ loan_summary_comparison.html
│  │  └─ ...
│  ├─ views.py
│  ├─ models.py
│  ├─ forms.py
│  └─ ...
└─ ...

💡 ทิป/ทริกที่พบบ่อย

Template ฟอร์แมตตัวเลข
หากใช้ตัวกรอง intcomma ต้องใส่ที่หัวเทมเพลต:

{% load humanize %}


หรือใช้ JS ฟอร์แมต toLocaleString('th-TH') แทนได้

ติดพอร์ต 8000 แล้ว

python manage.py runserver 0.0.0.0:8001


Migration ไม่ขึ้น / ไม่เจอตาราง
ตรวจสอบว่าเลือก DATABASE ถูก ต้อง makemigrations และ migrate ใหม่

Static files ในโปรดักชัน
ตั้งค่า STATIC_ROOT แล้วรัน:

python manage.py collectstatic