# management/commands/populate_thai_banks.py
# Django management command to populate Thai banks with comprehensive data

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from refinance.models import (
    Bank, LoanProduct, Promotion, FeeType, Fee, 
    Province, InterestRateHistory
)
from django.contrib.auth.models import User
import random
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Populate Thai banks with comprehensive data including promotions and loan products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all bank data before populating',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting bank data...')
            Bank.objects.all().delete()
            LoanProduct.objects.all().delete()
            Promotion.objects.all().delete()
            Fee.objects.all().delete()
            InterestRateHistory.objects.all().delete()

        self.stdout.write('Creating fee types...')
        self.create_fee_types()
        
        self.stdout.write('Creating provinces...')
        self.create_provinces()
        
        self.stdout.write('Creating Thai banks...')
        self.create_thai_banks()
        
        self.stdout.write('Creating loan products...')
        self.create_loan_products()
        
        self.stdout.write('Creating promotions...')
        self.create_promotions()
        
        self.stdout.write('Creating fees...')
        self.create_fees()
        
        self.stdout.write('Creating interest rate history...')
        self.create_interest_rate_history()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated Thai banks database')
        )

    def create_fee_types(self):
        """สร้างประเภทค่าธรรมเนียมต่างๆ"""
        fee_types = [
            ('processing_fee', 'ค่าธรรมเนียมจัดการ', 'percentage'),
            ('appraisal_fee', 'ค่าประเมินทรัพย์สิน', 'fixed'),
            ('legal_fee', 'ค่าธรรมเนียมกฎหมาย', 'fixed'),
            ('insurance_fee', 'ค่าเบี้ยประกันชีวิต', 'percentage'),
            ('property_insurance_fee', 'ค่าเบี้ยประกันอัคคีภัย', 'fixed'),
            ('transfer_fee', 'ค่าธรรมเนียมโอน', 'percentage'),
            ('mortgage_fee', 'ค่าจดจำนอง', 'percentage'),
            ('early_payment_fee', 'ค่าปรับชำระก่อนกำหนด', 'percentage'),
        ]
        
        for code, name, fee_type in fee_types:
            FeeType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'fee_type': fee_type,
                    'is_active': True
                }
            )

    def create_provinces(self):
        """สร้างข้อมูลจังหวัด"""
        provinces_data = [
            ('กรุงเทพมหานคร', 'Bangkok', 'central'),
            ('นนทบุรี', 'Nonthaburi', 'central'),
            ('ปทุมธานี', 'Pathum Thani', 'central'),
            ('สมุทรปราการ', 'Samut Prakan', 'central'),
            ('เชียงใหม่', 'Chiang Mai', 'north'),
            ('ภูเก็ต', 'Phuket', 'south'),
            ('ขอนแก่น', 'Khon Kaen', 'northeast'),
            ('ชลบุรี', 'Chonburi', 'east'),
            ('ระยอง', 'Rayong', 'east'),
            ('สงขลา', 'Songkhla', 'south'),
        ]
        
        for name, name_en, region in provinces_data:
            Province.objects.get_or_create(
                name=name,
                defaults={
                    'name_en': name_en,
                    'region': region,
                    'is_active': True
                }
            )

    def create_thai_banks(self):
        """สร้างข้อมูลธนาคารไทยทั้งหมด"""
        
        # ธนาคารพาณิชย์ไทย
        commercial_banks = [
            ('BBL', 'ธนาคารกรุงเทพ', 'Bangkok Bank', 'private', '#1f4e79', True),
            ('KTB', 'ธนาคารกรุงไทย', 'Krung Thai Bank', 'government', '#0066cc', True),
            ('BAY', 'ธนาคารกรุงศรีอยุธยา', 'Bank of Ayudhya', 'private', '#ff6600', True),
            ('KBANK', 'ธนาคารกสิกรไทย', 'Kasikornbank', 'private', '#4caf50', True),
            ('KKP', 'ธนาคารเกียรตินาคินภัทร', 'Kiatnakin Phatra Bank', 'private', '#ff9800', True),
            ('CIMB', 'ธนาคารซีไอเอ็มบี ไทย', 'CIMB Thai Bank', 'foreign', '#dc143c', True),
            ('TTB', 'ธนาคารทหารไทยธนชาต', 'TMBThanachart Bank', 'private', '#800080', True),
            ('TISCO', 'ธนาคารทิสโก้', 'Tisco Bank', 'private', '#ff4500', False),
            ('TCD', 'ธนาคารไทยเครดิต', 'Thai Credit Bank', 'private', '#228b22', False),
            ('SCB', 'ธนาคารไทยพาณิชย์', 'Siam Commercial Bank', 'private', '#9c27b0', True),
            ('UOB', 'ธนาคารยูโอบี', 'United Overseas Bank', 'foreign', '#0d47a1', True),
            ('LH', 'ธนาคารแลนด์ แอนด์ เฮ้าส์', 'Land and Houses Bank', 'private', '#f57c00', True),
        ]
        
        # ธนาคารของรัฐ
        government_banks = [
            ('GSB', 'ธนาคารออมสิน', 'Government Savings Bank', 'government', '#1976d2', True),
            ('BAAC', 'ธนาคารเพื่อการเกษตรและสหกรณ์การเกษตร', 'Bank for Agriculture and Agricultural Cooperatives', 'government', '#388e3c', True),
            ('GHB', 'ธนาคารอาคารสงเคราะห์', 'Government Housing Bank', 'government', '#f57c00', True),
            ('EXIM', 'ธนาคารเพื่อการส่งออกและนำเข้าแห่งประเทศไทย', 'Export-Import Bank of Thailand', 'government', '#795548', False),
            ('IBANK', 'ธนาคารอิสลามแห่งประเทศไทย', 'Islamic Bank of Thailand', 'government', '#009688', False),
            ('SME', 'ธนาคารพัฒนาวิสาหกิจขนาดกลางและขนาดย่อมแห่งประเทศไทย', 'SME Development Bank', 'government', '#ff5722', False),
        ]
        
        # ธนาคารต่างประเทศ
        foreign_banks = [
            ('SC', 'ธนาคารสแตนดาร์ดชาร์เตอร์ด (ไทย)', 'Standard Chartered (Thai)', 'foreign', '#0f7b7c', False),
            ('ICBC', 'ธนาคารไอซีบีซี (ไทย)', 'Industrial and Commercial Bank of China (Thai)', 'foreign', '#cc0000', False),
            ('BOC', 'ธนาคารแห่งประเทศจีน (ไทย)', 'Bank of China (Thai)', 'foreign', '#cc0000', False),
            ('SMBC', 'ธนาคารซูมิโตโม มิตซุย ทรัสต์ (ไทย)', 'Sumitomo Mitsui Trust Bank (Thai)', 'foreign', '#0066cc', False),
            ('HSBC', 'ธนาคารฮ่องกงและเซี่ยงไฮ้แบงกิ้งคอร์ปอเรชั่น', 'Hongkong and Shanghai Banking Corporation', 'foreign', '#db0011', False),
            ('CITI', 'ธนาคารซิตี้แบงก์', 'Citibank', 'foreign', '#0066cc', False),
            ('DEUTSCHE', 'ธนาคารดอยซ์แบงก์', 'Deutsche Bank', 'foreign', '#0018a8', False),
            ('JPMC', 'ธนาคารเจพีมอร์แกน เชส', 'JPMorgan Chase Bank', 'foreign', '#0066cc', False),
            ('MEGA', 'ธนาคารเมกะ สากลพาณิชย์', 'Mega International Commercial Bank', 'foreign', '#ff6600', False),
        ]
        
        all_banks = commercial_banks + government_banks + foreign_banks
        
        for i, (code, name, name_en, bank_type, color, is_featured) in enumerate(all_banks):
            # สร้างข้อความการตลาดตามประเภทธนาคาร
            if bank_type == 'government':
                marketing_msg = "ธนาคารของรัฐ เชื่อถือได้ อัตราดอกเบี้ยพิเศษ"
            elif bank_type == 'foreign':
                marketing_msg = "ธนาคารต่างประเทศ มาตรฐานสากล"
            else:
                marketing_msg = "ธนาคารพาณิชย์ชั้นนำ บริการครบครัน"
            
            bank, created = Bank.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'bank_type': bank_type,
                    'website': f'https://www.{code.lower()}.co.th',
                    'contact_phone': f'0-2{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'contact_email': f'info@{code.lower()}.co.th',
                    'description': f'{name} - {marketing_msg}',
                    'is_active': True,
                    'display_order': i + 1,
                    'brand_color': color,
                    'is_featured': is_featured,
                    'marketing_message': marketing_msg,
                }
            )
            
            if created:
                self.stdout.write(f'Created bank: {bank.name}')

    def create_loan_products(self):
        """สร้างผลิตภัณฑ์สินเชื่อสำหรับแต่ละธนาคาร"""
        
        for bank in Bank.objects.all():
            # สร้างผลิตภัณฑ์รีไฟแนนซ์หลัก
            self.create_refinance_products(bank)
            
            # สร้างผลิตภัณฑ์สินเชื่อบ้าน
            self.create_home_loan_products(bank)

    def create_refinance_products(self, bank):
        """สร้างผลิตภัณฑ์รีไฟแนนซ์"""
        
        # กำหนดอัตราดอกเบี้ยตามประเภทธนาคาร
        if bank.bank_type == 'government':
            base_rate = Decimal('2.85')  # ธนาคารรัฐอัตราต่ำกว่า
        elif bank.bank_type == 'foreign':
            base_rate = Decimal('3.25')  # ธนาคารต่างประเทศอัตราสูงกว่า
        else:
            base_rate = Decimal('3.05')  # ธนาคารพาณิชย์ทั่วไป
        
        # เพิ่มความหลากหลายในอัตราดอกเบี้ย
        rate_variation = Decimal(str(random.uniform(-0.2, 0.3)))
        interest_rate = base_rate + rate_variation
        
        # ผลิตภัณฑ์รีไฟแนนซ์มาตรฐาน
        standard_refinance = LoanProduct.objects.create(
            bank=bank,
            name=f'รีไฟแนนซ์ {bank.name}',
            product_type='refinance',
            description=f'สินเชื่อรีไฟแนนซ์จาก{bank.name} อัตราดอกเบี้ยแข่งขันได้ เงื่อนไขยืดหยุ่น',
            interest_rate=interest_rate,
            interest_rate_type='floating',
            min_loan_amount=Decimal('500000'),
            max_loan_amount=Decimal('50000000'),
            max_ltv=90 if bank.bank_type == 'government' else 85,
            max_term_years=30,
            processing_fee=Decimal('0.5') if bank.bank_type == 'government' else Decimal('1.0'),
            appraisal_fee=Decimal('5000'),
            min_income=Decimal('25000'),
            is_active=True,
            is_popular=bank.is_featured,
            display_order=1
        )
        
        # ผลิตภัณฑ์รีไฟแนนซ์พรีเมี่ยม (สำหรับธนาคารใหญ่)
        if bank.is_featured:
            premium_refinance = LoanProduct.objects.create(
                bank=bank,
                name=f'รีไฟแนนซ์พรีเมี่ยม {bank.name}',
                product_type='refinance',
                description=f'สินเชื่อรีไฟแนนซ์พรีเมี่ยม สำหรับลูกค้าที่มีรายได้สูง อัตราดอกเบี้ยพิเศษ',
                interest_rate=interest_rate - Decimal('0.25'),
                interest_rate_type='floating',
                min_loan_amount=Decimal('2000000'),
                max_loan_amount=Decimal('100000000'),
                max_ltv=95,
                max_term_years=35,
                processing_fee=Decimal('0.25'),
                appraisal_fee=Decimal('3000'),
                min_income=Decimal('100000'),
                is_active=True,
                is_popular=True,
                display_order=2
            )

    def create_home_loan_products(self, bank):
        """สร้างผลิตภัณฑ์สินเชื่อบ้าน"""
        
        # กำหนดอัตราดอกเบี้ยตามประเภทธนาคาร
        if bank.bank_type == 'government':
            base_rate = Decimal('2.95')
        elif bank.bank_type == 'foreign':
            base_rate = Decimal('3.35')
        else:
            base_rate = Decimal('3.15')
        
        rate_variation = Decimal(str(random.uniform(-0.15, 0.25)))
        interest_rate = base_rate + rate_variation
        
        # สินเชื่อบ้านมาตรฐาน
        home_loan = LoanProduct.objects.create(
            bank=bank,
            name=f'สินเชื่อบ้าน {bank.name}',
            product_type='home_loan',
            description=f'สินเชื่อเพื่อซื้อบ้านจาก{bank.name} อัตราดอกเบี้ยคงที่ช่วงแรก',
            interest_rate=interest_rate,
            interest_rate_type='mixed',
            min_loan_amount=Decimal('300000'),
            max_loan_amount=Decimal('20000000'),
            max_ltv=95,
            max_term_years=30,
            processing_fee=Decimal('1.0'),
            appraisal_fee=Decimal('5000'),
            min_income=Decimal('20000'),
            is_active=True,
            display_order=3
        )

    def create_promotions(self):
        """สร้างโปรโมชั่นสำหรับแต่ละธนาคาร"""
        
        current_date = timezone.now().date()
        
        for bank in Bank.objects.all():
            # โปรโมชั่นอัตราดอกเบี้ยพิเศษ
            special_rate_promo = Promotion.objects.create(
                bank=bank,
                title=f'อัตราดอกเบี้ยพิเศษ {bank.name}',
                description=f'อัตราดอกเบี้ยพิเศษ 2.49% ปีแรก สำหรับลูกค้าที่รีไฟแนนซ์มาที่ {bank.name}',
                promotion_type='special_rate',
                min_loan_amount=Decimal('1000000'),
                max_loan_amount=Decimal('50000000'),
                special_rate=Decimal('2.49'),
                special_rate_period=12,
                start_date=current_date - timedelta(days=30),
                end_date=current_date + timedelta(days=60),
                is_active=True,
                is_sponsored=bank.is_featured,
                priority=10 if bank.is_featured else 5,
                terms_conditions=f'เงื่อนไข: วงเงินขั้นต่ำ 1 ล้านบาท, อัตราพิเศษ 12 เดือนแรก, หลังจากนั้นใช้อัตราตาม {bank.name} กำหนด'
            )
            
            # โปรโมชั่นยกเว้นค่าธรรมเนียม (สำหรับธนาคารใหญ่)
            if bank.is_featured:
                fee_waiver_promo = Promotion.objects.create(
                    bank=bank,
                    title=f'ยกเว้นค่าธรรมเนียมจัดการ {bank.name}',
                    description=f'ยกเว้นค่าธรรมเนียมจัดการ 100% สำหรับลูกค้าที่รีไฟแนนซ์ใหม่',
                    promotion_type='fee_waiver',
                    min_loan_amount=Decimal('500000'),
                    start_date=current_date - timedelta(days=15),
                    end_date=current_date + timedelta(days=45),
                    is_active=True,
                    is_sponsored=True,
                    priority=8,
                    terms_conditions='เงื่อนไข: สำหรับลูกค้าใหม่ที่ยื่นสมัครภายในระยะเวลาโปรโมชั่น'
                )
            
            # โปรโมชั่นเงินคืน (สำหรับธนาคารพิเศษ)
            if bank.code in ['SCB', 'KBANK', 'BBL']:
                cashback_promo = Promotion.objects.create(
                    bank=bank,
                    title=f'เงินคืน {bank.name}',
                    description=f'รับเงินคืนสูงสุด 50,000 บาท เมื่อรีไฟแนนซ์กับ {bank.name}',
                    promotion_type='cashback',
                    min_loan_amount=Decimal('3000000'),
                    start_date=current_date - timedelta(days=45),
                    end_date=current_date + timedelta(days=75),
                    is_active=True,
                    is_sponsored=True,
                    priority=15,
                    terms_conditions='เงื่อนไข: วงเงินขั้นต่ำ 3 ล้านบาท, เงินคืนตามเงื่อนไขที่ธนาคารกำหนด'
                )

    def create_fees(self):
        """สร้างค่าธรรมเนียมสำหรับแต่ละธนาคาร"""
        
        fee_types = FeeType.objects.all()
        
        for bank in Bank.objects.all():
            for fee_type in fee_types:
                # กำหนดค่าธรรมเนียมตามประเภทธนาคาร
                if bank.bank_type == 'government':
                    fee_multiplier = 0.8  # ธนาคารรัฐค่าธรรมเนียมต่ำกว่า
                elif bank.bank_type == 'foreign':
                    fee_multiplier = 1.2  # ธนาคารต่างประเทศค่าธรรมเนียมสูงกว่า
                else:
                    fee_multiplier = 1.0  # ธนาคารพาณิชย์ทั่วไป
                
                # กำหนดค่าธรรมเนียมตามประเภท
                if fee_type.code == 'processing_fee':
                    amount = Decimal('1.0') * Decimal(str(fee_multiplier))
                elif fee_type.code == 'appraisal_fee':
                    amount = Decimal('5000') * Decimal(str(fee_multiplier))
                elif fee_type.code == 'legal_fee':
                    amount = Decimal('8000') * Decimal(str(fee_multiplier))
                elif fee_type.code == 'insurance_fee':
                    amount = Decimal('0.5') * Decimal(str(fee_multiplier))
                elif fee_type.code == 'property_insurance_fee':
                    amount = Decimal('3000') * Decimal(str(fee_multiplier))
                elif fee_type.code == 'transfer_fee':
                    amount = Decimal('0.01') * Decimal(str(fee_multiplier))
                elif fee_type.code == 'mortgage_fee':
                    amount = Decimal('0.01') * Decimal(str(fee_multiplier))
                elif fee_type.code == 'early_payment_fee':
                    amount = Decimal('2.0') * Decimal(str(fee_multiplier))
                else:
                    amount = Decimal('1000') * Decimal(str(fee_multiplier))
                
                # กำหนดขั้นต่ำและสูงสุด
                if fee_type.fee_type == 'percentage':
                    min_amount = Decimal('1000') if fee_type.code != 'transfer_fee' else Decimal('500')
                    max_amount = Decimal('50000') if fee_type.code == 'processing_fee' else Decimal('20000')
                else:
                    min_amount = None
                    max_amount = None
                
                Fee.objects.create(
                    bank=bank,
                    fee_type=fee_type,
                    amount=amount,
                    min_amount=min_amount,
                    max_amount=max_amount,
                    is_active=True
                )

    def create_interest_rate_history(self):
        """สร้างประวัติอัตราดอกเบี้ย"""
        
        # สร้างประวัติย้อนหลัง 6 เดือน
        current_date = timezone.now().date()
        
        for loan_product in LoanProduct.objects.all():
            for i in range(6):
                history_date = current_date - timedelta(days=30 * i)
                
                # อัตราดอกเบี้ยในอดีตสูงกว่าปัจจุบันเล็กน้อย
                historical_rate = loan_product.interest_rate + Decimal(str(i * 0.05))
                
                InterestRateHistory.objects.create(
                    bank=loan_product.bank,
                    loan_product=loan_product,
                    interest_rate=historical_rate,
                    effective_date=history_date,
                    notes=f'อัตราดอกเบี้ย ณ วันที่ {history_date.strftime("%d/%m/%Y")}',
                    created_by=None  # ไม่มี user ในขณะนี้
                )

    def get_random_admin_user(self):
        """ดึง admin user แบบสุ่ม (ถ้ามี)"""
        try:
            admin_users = User.objects.filter(is_staff=True)
            if admin_users.exists():
                return admin_users.first()
        except:
            pass
        return None