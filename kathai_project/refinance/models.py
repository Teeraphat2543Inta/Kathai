from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

class Province(models.Model):
    """จังหวัด"""
    REGION_CHOICES = [
        ('north', 'ภาคเหนือ'),
        ('northeast', 'ภาคตะวันออกเฉียงเหนือ'),
        ('central', 'ภาคกลาง'),
        ('east', 'ภาคภาคตะวันออก'),
        ('west', 'ภาคตะวันตก'),
        ('south', 'ภาคใต้'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='ชื่อจังหวัด')
    name_en = models.CharField(max_length=100, verbose_name='ชื่อจังหวัด (อังกฤษ)', blank=True)
    region = models.CharField(max_length=20, choices=REGION_CHOICES, verbose_name='ภาค')
    is_active = models.BooleanField(default=True, verbose_name='ใช้งาน')
    display_order = models.IntegerField(default=0, verbose_name='ลำดับการแสดง')
    
    class Meta:
        verbose_name = 'จังหวัด'
        verbose_name_plural = 'จังหวัด'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name

class Bank(models.Model):
    """ธนาคาร"""
    BANK_TYPE_CHOICES = [
        ('government', 'ธนาคารรัฐ'),
        ('private', 'ธนาคารเอกชน'),
        ('foreign', 'ธนาคารต่างประเทศ'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='ชื่อธนาคาร')
    code = models.CharField(max_length=10, unique=True, verbose_name='รหัสธนาคาร')
    bank_type = models.CharField(max_length=20, choices=BANK_TYPE_CHOICES, default='private', verbose_name='ประเภทธนาคาร')
    logo = models.ImageField(upload_to='bank_logos/', blank=True, null=True, verbose_name='โลโก้') # แก้ไข: ลบฟิลด์ logo ที่ซ้ำซ้อนออก
    website = models.URLField(blank=True, verbose_name='เว็บไซต์')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='เบอร์ติดต่อ')
    contact_email = models.EmailField(blank=True, verbose_name='อีเมลติดต่อ')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    is_active = models.BooleanField(default=True, verbose_name='ใช้งาน')
    display_order = models.IntegerField(default=0, verbose_name='ลำดับการแสดง')
    brand_color = models.CharField(max_length=7, default='#007bff', verbose_name='สีแบรนด์', help_text='รหัสสี Hex เช่น #FF0000')
    
    # ข้อมูลการตลาด
    is_featured = models.BooleanField(default=False, verbose_name='แนะนำพิเศษ')
    marketing_message = models.CharField(max_length=200, blank=True, verbose_name='ข้อความการตลาด')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไข')
    
    class Meta:
        verbose_name = 'ธนาคาร'
        verbose_name_plural = 'ธนาคาร'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_active_promotions(self):
        """โปรโมชั่นที่ใช้งานได้"""
        from django.utils import timezone
        return self.promotions.filter(
            is_active=True,
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        )

class LoanProduct(models.Model):
    """ผลิตภัณฑ์สินเชื่อ"""
    PRODUCT_TYPE_CHOICES = [
        ('home_loan', 'สินเชื่อบ้าน'),
        ('refinance', 'รีไฟแนนซ์'),
        ('home_equity', 'สินเชื่อเพื่อบ้าน'),
        ('construction', 'สินเชื่อก่อสร้าง'),
    ]
    
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='loan_products', verbose_name='ธนาคาร')
    name = models.CharField(max_length=100, verbose_name='ชื่อผลิตภัณฑ์')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, verbose_name='ประเภทสินเชื่อ')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    
    # อัตราดอกเบี้ย
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='อัตราดอกเบี้ย (%)')
    interest_rate_type = models.CharField(max_length=20, choices=[
        ('fixed', 'อัตราคงที่'),
        ('floating', 'อัตราลอยตัว'),
        ('mixed', 'อัตราผสม'),
    ], default='floating', verbose_name='ประเภทอัตราดอกเบี้ย')
    
    # วงเงินกู้
    min_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='วงเงินกู้ขั้นต่ำ (บาท)')
    max_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='วงเงินกู้สูงสุด (บาท)')
    
    # LTV และระยะเวลา
    max_ltv = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], 
                                 verbose_name='LTV สูงสุด (%)', help_text='Loan to Value Ratio')
    max_term_years = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)], 
                                       verbose_name='ระยะเวลากู้สูงสุด (ปี)')
    
    # ค่าธรรมเนียม
    processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                       verbose_name='ค่าธรรมเนียมจัดการ (%)')
    appraisal_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                      verbose_name='ค่าประเมินทรัพย์ (บาท)')
    
    # เงื่อนไข
    min_income = models.DecimalField(max_digits=12, decimal_places=2, default=15000, 
                                   verbose_name='รายได้ขั้นต่ำ (บาท/เดือน)')
    min_age = models.IntegerField(default=20, verbose_name='อายุขั้นต่ำ (ปี)')
    max_age = models.IntegerField(default=65, verbose_name='อายุสูงสุด (ปี)')
    
    # การตั้งค่า
    is_active = models.BooleanField(default=True, verbose_name='ใช้งาน')
    is_popular = models.BooleanField(default=False, verbose_name='ยอดนิยม')
    display_order = models.IntegerField(default=0, verbose_name='ลำดับการแสดง')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไข')
    
    class Meta:
        verbose_name = 'ผลิตภัณฑ์สินเชื่อ'
        verbose_name_plural = 'ผลิตภัณฑ์สินเชื่อ'
        ordering = ['bank__name', 'display_order', 'name']
    
    def __str__(self):
        return f"{self.bank.name} - {self.name}"

class Promotion(models.Model):
    """โปรโมชั่น"""
    PROMOTION_TYPE_CHOICES = [
        ('special_rate', 'อัตราดอกเบี้ยพิเศษ'),
        ('fee_waiver', 'ยกเว้นค่าธรรมเนียม'),
        ('cashback', 'เงินคืน'),
        ('gift', 'ของแถม'),
        ('other', 'อื่นๆ'),
    ]
    
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='promotions', verbose_name='ธนาคาร')
    title = models.CharField(max_length=200, verbose_name='ชื่อโปรโมชั่น')
    description = models.TextField(verbose_name='รายละเอียด')
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPE_CHOICES, verbose_name='ประเภทโปรโมชั่น')
    
    # เงื่อนไขโปรโมชั่น
    min_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, 
                                        verbose_name='วงเงินกู้ขั้นต่ำ (บาท)')
    max_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, 
                                        verbose_name='วงเงินกู้สูงสุด (บาท)')
    
    # อัตราดอกเบี้ยพิเศษ
    special_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, 
                                     verbose_name='อัตราดอกเบี้ยพิเศษ (%)')
    special_rate_period = models.IntegerField(blank=True, null=True, 
                                            verbose_name='ระยะเวลาอัตราพิเศษ (เดือน)')
    
    # ระยะเวลาโปรโมชั่น
    start_date = models.DateField(verbose_name='วันเริ่มโปรโมชั่น')
    end_date = models.DateField(verbose_name='วันสิ้นสุดโปรโมชั่น')
    
    # การตั้งค่า
    is_active = models.BooleanField(default=True, verbose_name='ใช้งาน')
    is_sponsored = models.BooleanField(default=False, verbose_name='โปรโมชั่นสปอนเซอร์')
    priority = models.IntegerField(default=0, verbose_name='ลำดับความสำคัญ', 
                                 help_text='เลขมากขึ้นจะแสดงก่อน')
    
    # ข้อมูลการตลาด
    banner_image = models.ImageField(upload_to='promotion_banners/', blank=True, null=True, 
                                   verbose_name='รูปป้ายโปรโมชั่น')
    terms_conditions = models.TextField(blank=True, verbose_name='ข้อกำหนดและเงื่อนไข')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไข')
    
    class Meta:
        verbose_name = 'โปรโมชั่น'
        verbose_name_plural = 'โปรโมชั่น'
        ordering = ['-is_sponsored', '-priority', '-start_date']
    
    def __str__(self):
        return f"{self.bank.name} - {self.title}"
    
    def is_valid_now(self):
        """ตรวจสอบว่าโปรโมชั่นยังใช้ได้หรือไม่"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date

class FeeType(models.Model):
    """ประเภทค่าธรรมเนียม"""
    name = models.CharField(max_length=100, verbose_name='ชื่อค่าธรรมเนียม')
    code = models.CharField(max_length=50, unique=True, verbose_name='รหัส')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    fee_type = models.CharField(max_length=20, choices=[
        ('percentage', 'เปอร์เซ็นต์'),
        ('fixed', 'ค่าคงที่'),
    ], verbose_name='ประเภทค่าธรรมเนียม')
    is_active = models.BooleanField(default=True, verbose_name='ใช้งาน')
    
    class Meta:
        verbose_name = 'ประเภทค่าธรรมเนียม'
        verbose_name_plural = 'ประเภทค่าธรรมเนียม'
    
    def __str__(self):
        return self.name

class Fee(models.Model):
    """ค่าธรรมเนียมของธนาคาร"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='fees', verbose_name='ธนาคาร')
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE, verbose_name='ประเภทค่าธรรมเนียม')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='จำนวน')
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
                                   verbose_name='จำนวนขั้นต่ำ (บาท)')
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
                                   verbose_name='จำนวนสูงสุด (บาท)')
    is_active = models.BooleanField(default=True, verbose_name='ใช้งาน')
    
    class Meta:
        verbose_name = 'ค่าธรรมเนียม'
        verbose_name_plural = 'ค่าธรรมเนียม'
        unique_together = ['bank', 'fee_type']
    
    def __str__(self):
        return f"{self.bank.name} - {self.fee_type.name}: {self.amount}"

class Property(models.Model):
    """ทรัพย์สิน"""
    PROPERTY_TYPE_CHOICES = [
        ('house', 'บ้านเดี่ยว'),
        ('townhouse', 'ทาวน์เฮ้าส์'),
        ('condo', 'คอนโดมิเนียม'),
        ('apartment', 'อพาร์ทเมนต์'),
        ('commercial', 'อาคารพาณิชย์'),
        ('land', 'ที่ดิน'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties', verbose_name='เจ้าของ')
    name = models.CharField(max_length=200, verbose_name='ชื่อทรัพย์สิน')
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, verbose_name='ประเภท')
    
    # ที่อยู่
    address = models.TextField(verbose_name='ที่อยู่')
    province = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name='จังหวัด')
    postal_code = models.CharField(max_length=10, blank=True, verbose_name='รหัสไปรษณีย์')
    
    # มูลค่าและการประเมิน
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='มูลค่าประเมิน (บาท)')
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, 
                                       verbose_name='ราคาซื้อ (บาท)')
    purchase_date = models.DateField(blank=True, null=True, verbose_name='วันที่ซื้อ')
    
    # ข้อมูลเพิ่มเติม
    land_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
                                  verbose_name='ขนาดที่ดิน (ตร.ว.)')
    building_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
                                      verbose_name='ขนาดอาคาร (ตร.ม.)')
    
    # สินเชื่อปัจจุบัน
    has_existing_loan = models.BooleanField(default=False, verbose_name='มีสินเชื่ออยู่')
    existing_loan_balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, 
                                              verbose_name='ยอดคงเหลือ (บาท)')
    existing_bank = models.ForeignKey(Bank, on_delete=models.SET_NULL, blank=True, null=True, 
                                    related_name='existing_loans', verbose_name='ธนาคารปัจจุบัน')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไข')
    
    class Meta:
        verbose_name = 'ทรัพย์สิน'
        verbose_name_plural = 'ทรัพย์สิน'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"

class LoanApplication(models.Model):
    """ใบสมัครสินเชื่อ"""
    STATUS_CHOICES = [
        ('draft', 'ร่าง'),
        ('submitted', 'ยื่นแล้ว'),
        ('under_review', 'กำลังพิจารณา'),
        ('approved', 'อนุมัติ'),
        ('rejected', 'ปฏิเสธ'),
        ('cancelled', 'ยกเลิก'),
    ]
    
    # ข้อมูลพื้นฐาน
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications', verbose_name='ผู้สมัคร')
    application_no = models.CharField(max_length=20, unique=True, verbose_name='เลขที่ใบสมัคร')
    
    # ข้อมูลสินเชื่อ
    property = models.ForeignKey(Property, on_delete=models.CASCADE, verbose_name='ทรัพย์สิน')
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='จำนวนเงินกู้ (บาท)')
    loan_term = models.IntegerField(verbose_name='ระยะเวลากู้ (ปี)')
    purpose = models.CharField(max_length=100, default='refinance', verbose_name='วัตถุประสงค์')
    
    # ข้อมูลทางการเงิน
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='รายได้ต่อเดือน (บาท)')
    monthly_expense = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='รายจ่ายต่อเดือน (บาท)')
    other_debts = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='หนี้สินอื่น (บาท)')
    
    # สถานะและการติดตาม
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='สถานะ')
    submitted_at = models.DateTimeField(blank=True, null=True, verbose_name='วันที่ยื่น')
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name='วันที่พิจารณา')
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name='วันที่อนุมัติ')
    
    # หมายเหตุ
    notes = models.TextField(blank=True, verbose_name='หมายเหตุ')
    admin_notes = models.TextField(blank=True, verbose_name='หมายเหตุแอดมิน')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไข')
    applied_bank_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'ใบสมัครสินเชื่อ'
        verbose_name_plural = 'ใบสมัครสินเชื่อ'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.application_no} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.application_no:
            # สร้างเลขที่ใบสมัครอัตโนมัติ
            from django.utils import timezone
            prefix = timezone.now().strftime('%Y%m')
            last_app = LoanApplication.objects.filter(
                application_no__startswith=prefix
            ).order_by('-application_no').first()
            
            if last_app:
                last_num = int(last_app.application_no[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
                
            self.application_no = f"{prefix}{new_num:04d}"
        
        super().save(*args, **kwargs)

class ApplicationBank(models.Model):
    """ธนาคารที่ยื่นสมัคร"""
    application = models.ForeignKey(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name='application_banks',
        verbose_name='ใบสมัคร'
    )
    bank = models.ForeignKey(
        Bank,
        on_delete=models.CASCADE,
        verbose_name='ธนาคาร'
    )
    loan_product = models.ForeignKey(
        LoanProduct,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='ผลิตภัณฑ์สินเชื่อ'
    )
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='โปรโมชั่น'
    )
    
    # ผลการพิจารณา
    status = models.CharField(
        max_length=20,
        choices=LoanApplication.STATUS_CHOICES,
        default='submitted',
        verbose_name='สถานะ'
    )
    offered_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='อัตราดอกเบี้ยที่เสนอ (%)'
    )
    offered_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='วงเงินที่อนุมัติ (บาท)'
    )
    
    # การติดตาม
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่ยื่น')
    response_at = models.DateTimeField(blank=True, null=True, verbose_name='วันที่ตอบกลับ')
    notes = models.TextField(blank=True, verbose_name='หมายเหตุ')

    # ========= Snapshot ข้อมูลติดต่อธนาคาร ณ วันที่ยื่น =========
    contact_phone_snapshot = models.CharField(max_length=50, blank=True, default='', verbose_name='เบอร์โทรติดต่อ')
    contact_email_snapshot = models.EmailField(blank=True, default='', verbose_name='อีเมลติดต่อ')

    # ========= Snapshot รายละเอียดสินเชื่อที่ยื่น =========
    product_name_snapshot = models.CharField(max_length=255, blank=True, default='', verbose_name='ชื่อผลิตภัณฑ์ตอนยื่น')
    interest_rate_snapshot = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, verbose_name='อัตราดอกเบี้ย (%)')
    max_ltv_snapshot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='LTV สูงสุด (%)')
    max_term_years_snapshot = models.IntegerField(null=True, blank=True, verbose_name='ระยะเวลากู้สูงสุด (ปี)')
    processing_fee_percent_snapshot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='ค่าธรรมเนียม (%)')
    product_note_snapshot = models.TextField(blank=True, default='', verbose_name='หมายเหตุผลิตภัณฑ์')

    class Meta:
        verbose_name = 'การยื่นสมัครต่อธนาคาร'
        verbose_name_plural = 'การยื่นสมัครต่อธนาคาร'
        unique_together = ['application', 'bank']
    
    def __str__(self):
        return f"{self.application.application_no} - {self.bank.name}"

class Document(models.Model):
    """เอกสาร"""
    DOCUMENT_TYPE_CHOICES = [
        ('id_card', 'บัตรประชาชน'),
        ('house_registration', 'ทะเบียนบ้าน'),
        ('income_statement', 'หลักฐานรายได้'),
        ('bank_statement', 'สลิปเงินเดือน'),
        ('property_document', 'เอกสารสิทธิ์ทรัพย์สิน'),
        ('appraisal_report', 'รายงานการประเมิน'),
        ('other', 'อื่นๆ'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents', verbose_name='เจ้าของ')
    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, 
                                  blank=True, null=True, related_name='documents', verbose_name='ใบสมัคร')
    
    name = models.CharField(max_length=200, verbose_name='ชื่อเอกสาร')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES, verbose_name='ประเภทเอกสาร')
    file = models.FileField(upload_to='documents/', verbose_name='ไฟล์')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    
    is_verified = models.BooleanField(default=False, verbose_name='ตรวจสอบแล้ว')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                  related_name='verified_documents', verbose_name='ผู้ตรวจสอบ')
    verified_at = models.DateTimeField(blank=True, null=True, verbose_name='วันที่ตรวจสอบ')
    
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่อัปโหลด')
    
    class Meta:
        verbose_name = 'เอกสาร'
        verbose_name_plural = 'เอกสาร'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"

class ActivityLog(models.Model):
    """บันทึกการใช้งาน"""
    ACTIVITY_TYPE_CHOICES = [
        ('login', 'เข้าสู่ระบบ'),
        ('logout', 'ออกจากระบบ'),
        ('register', 'สมัครสมาชิก'),
        ('profile_update', 'อัปเดตโปรไฟล์'),
        ('property_add', 'เพิ่มทรัพย์สิน'),
        ('loan_comparison', 'เปรียบเทียบสินเชื่อ'),
        ('loan_application', 'ยื่นใบสมัครสินเชื่อ'),
        ('document_upload', 'อัปโหลดเอกสาร'),
        ('page_view', 'เข้าดูหน้า'),
        ('other', 'อื่นๆ'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, 
                           related_name='activity_logs', verbose_name='ผู้ใช้')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPE_CHOICES, verbose_name='ประเภทกิจกรรม')
    description = models.CharField(max_length=500, verbose_name='รายละเอียด')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP Address')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    details = models.JSONField(blank=True, null=True, verbose_name='ข้อมูลเพิ่มเติม')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่')
    
    class Meta:
        verbose_name = 'บันทึกการใช้งาน'
        verbose_name_plural = 'บันทึกการใช้งาน'
        ordering = ['-created_at']
    
    def __str__(self):
        user_name = self.user.username if self.user else 'ไม่ระบุ'
        return f"{user_name} - {self.get_activity_type_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

class SystemSetting(models.Model):
    """การตั้งค่าระบบ"""
    SETTING_TYPE_CHOICES = [
        ('text', 'ข้อความ'),
        ('number', 'ตัวเลข'),
        ('boolean', 'เปิด/ปิด'),
        ('json', 'JSON'),
    ]
    
    key = models.CharField(max_length=100, unique=True, verbose_name='คีย์')
    value = models.TextField(verbose_name='ค่า')
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPE_CHOICES, 
                                  default='text', verbose_name='ประเภท')
    description = models.CharField(max_length=200, blank=True, verbose_name='คำอธิบาย')
    category = models.CharField(max_length=50, default='general', verbose_name='หมวดหมู่')
    is_public = models.BooleanField(default=False, verbose_name='แสดงสาธารณะ')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไข')
    
    class Meta:
        verbose_name = 'การตั้งค่าระบบ'
        verbose_name_plural = 'การตั้งค่าระบบ'
        ordering = ['category', 'key']

    def __str__(self):
        return f"{self.key}: {self.value}"
    
    def get_value(self):
        """แปลงค่าตามประเภท"""
        if self.setting_type == 'number':
            try:
                return float(self.value)
            except ValueError:
                return 0
        elif self.setting_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes', 'on']
        elif self.setting_type == 'json':
            try:
                import json
                return json.loads(self.value)
            except (ValueError, TypeError):
                return {}
        return self.value

class InterestRateHistory(models.Model):
    """ประวัติอัตราดอกเบี้ย"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='rate_history', verbose_name='ธนาคาร')
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.CASCADE, 
                                   related_name='rate_history', verbose_name='ผลิตภัณฑ์สินเชื่อ')
    
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='อัตราดอกเบี้ย (%)')
    effective_date = models.DateField(verbose_name='วันที่มีผล')
    notes = models.CharField(max_length=200, blank=True, verbose_name='หมายเหตุ')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่บันทึก')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                 verbose_name='ผู้บันทึก')
    
    class Meta:
        verbose_name = 'ประวัติอัตราดอกเบี้ย'
        verbose_name_plural = 'ประวัติอัตราดอกเบี้ย'
        ordering = ['-effective_date', 'bank__name']
    
    def __str__(self):
        return f"{self.bank.name} - {self.interest_rate}% ({self.effective_date})"
    
    
    
class Advertisement(models.Model):
    title = models.CharField(max_length=200, verbose_name="หัวข้อ")
    description = models.TextField(verbose_name="รายละเอียด", blank=True, null=True)
    image = models.ImageField(upload_to='advertisements/', verbose_name="รูปภาพโฆษณา", blank=True, null=True)
    link = models.URLField(max_length=500, verbose_name="ลิงก์ (URL)", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="แสดงผล")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขล่าสุด")

    class Meta:
        verbose_name = "โฆษณา/ข่าวสาร"
        verbose_name_plural = "โฆษณาและข่าวสาร"
        ordering = ['-created_at'] # เรียงลำดับจากใหม่ไปเก่า

    def __str__(self):
        return self.title


from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="ชื่อบทความ")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.TextField(verbose_name="บทสรุป", help_text="คำอธิบายสั้นๆ เกี่ยวกับบทความ")
    content = models.TextField(verbose_name="เนื้อหาเต็ม")
    image = models.ImageField(upload_to='article_images/', verbose_name="รูปภาพประกอบ", blank=True, null=True)
    published_date = models.DateTimeField(default=timezone.now, verbose_name="วันที่เผยแพร่")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-published_date']
        verbose_name = "บทความ"
        verbose_name_plural = "บทความ"