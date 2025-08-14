# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models.fields.json import JSONField # <--- ตรวจสอบให้แน่ใจว่ามีบรรทัดนี้

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class UserProfile(models.Model):
    INCOME_SOURCES = [
        ('salary', 'เงินเดือน'),
        ('business', 'ธุรกิจส่วนตัว'),
        ('freelance', 'อิสระ/ฟรีแลนซ์'),
        ('investment', 'การลงทุน'),
        ('other', 'อื่นๆ'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_regex = RegexValidator(regex=r'^[0-9]{9,15}$', message="รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง (อนุญาตเฉพาะตัวเลข 9-15 หลัก)")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    citizen_id = models.CharField(max_length=13, unique=True, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    income_source = models.CharField(max_length=20, choices=INCOME_SOURCES, blank=True, null=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    monthly_expenses = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # เพิ่มฟิลด์สำหรับเก็บสถานะการยอมรับข้อตกลง
    terms_accepted = models.BooleanField(default=False, verbose_name='ยอมรับข้อตกลงและเงื่อนไข')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "โปรไฟล์ผู้ใช้"
        verbose_name_plural = "โปรไฟล์ผู้ใช้"
        ordering = ['user__username']

    def __str__(self):
        full_name = self.user.get_full_name()
        if full_name:
            return f"{full_name}'s Profile"
        return f"{self.user.username}'s Profile"

# โมเดล ActivityLog ที่เพิ่มเข้ามาใหม่ (สำคัญสำหรับการบันทึก Log)
# โมเดล ActivityLog ที่ปรับปรุงใหม่
class ActivityLog(models.Model):
    # เพิ่ม related_name='accounts_activities' เพื่อไม่ให้ชนกับโมเดลอื่น
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts_activities', verbose_name="ผู้ใช้งาน", null=True, blank=True)
    activity_type = models.CharField(max_length=50, verbose_name="ประเภทกิจกรรม")
    description = models.CharField(max_length=255, verbose_name="คำอธิบายกิจกรรม")
    url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL ที่เข้าถึง")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="เวลา")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP Address")
    user_agent = models.CharField(max_length=500, blank=True, null=True, verbose_name="User Agent")
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name="Session Key")
    extra_data = JSONField(blank=True, null=True, verbose_name="ข้อมูลเพิ่มเติม")

    class Meta:
        verbose_name = "บันทึกการใช้งาน"
        verbose_name_plural = "บันทึกการใช้งาน"
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.activity_type} - {self.description} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
