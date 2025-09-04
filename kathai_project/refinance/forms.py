from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Property, LoanApplication, Document, LoanProduct, Bank, Province, Promotion
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import CheckboxSelectMultiple


# ตรวจสอบให้แน่ใจว่าได้นำเข้า UserProfile จาก accounts.models อย่างถูกต้อง
# หาก UserProfile อยู่ในแอปอื่น (เช่น refinance) ให้เปลี่ยน path ให้ถูกต้อง
from accounts.models import UserProfile 

# --- Global Choice Fields ---
PROPERTY_TYPE_CHOICES = [
    ('house', 'บ้าน (บ้านเดี่ยว, บ้านแฝด, ทาวน์เฮาส์, ทาวน์โฮม)'),
    ('condo', 'คอนโดมิเนียม (ห้องชุดพักอาศัย)'),
    ('commercial_business', 'ตึกพาณิชย์ (ใช้ประกอบธุรกิจ)'),
    ('commercial_residence', 'ตึกพาณิชย์ (ใช้พักอาศัย)'),
]

OCCUPATION_CHOICES = [
    ('employee', 'พนักงานบริษัท/รัฐวิสาหกิจ'),
    ('business_owner', 'เจ้าของกิจการ'),
    ('freelance', 'อาชีพอิสระ (ฟรีแลนซ์)'),
    ('special_profession', 'กลุ่มอาชีพพิเศษ (แพทย์, นักบิน, ผู้พิพากษา, อัยการ, อาจารย์ระดับ ผศ.)'),
    ('government', 'ข้าราชการ'),
    ('military_police', 'ทหาร/ตำรวจ'),
]

REMAINING_YEARS_CHOICES = [
    (str(i), f'{i} ปี') for i in range(1, 31)
] + [('30+', 'มากกว่า 30 ปี')]

YES_NO_CHOICES = [
    ('yes', 'ต้องการ'),
    ('no', 'ไม่ต้องการ'),
]

# --- Forms ---

class RefinanceComparisonForm(forms.Form):
    property_price = forms.DecimalField(
        label="ราคาบ้าน/คอนโดที่ซื้อ (บาท)",
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'placeholder': 'เช่น 5,000,000', 'min': '0'})
    )
    current_loan_balance = forms.DecimalField(
        label="ยอดหนี้บ้านคงเหลือ (บาท)",
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'placeholder': 'เช่น 3,000,000', 'min': '0'})
    )
    monthly_income = forms.DecimalField(
        label="รายได้รวมต่อเดือน (บาท)",
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'placeholder': 'เช่น 80,000', 'min': '0'})
    )
    remaining_years = forms.ChoiceField(
        label="ระยะเวลาผ่อนที่เหลือ (ปี)",
        choices=REMAINING_YEARS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        property_price = cleaned_data.get('property_price')
        current_loan_balance = cleaned_data.get('current_loan_balance')

        if property_price and current_loan_balance and current_loan_balance > property_price:
            self.add_error('current_loan_balance', "ยอดหนี้คงเหลือไม่ควรเกินราคาบ้าน")
        return cleaned_data


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'property_type', 'address', 'province', 'postal_code',
                 'estimated_value', 'purchase_price', 'purchase_date',
                 'land_size', 'building_size', 'has_existing_loan',
                 'existing_loan_balance', 'existing_bank']
        labels = {
            'name': 'ชื่อทรัพย์สิน',
            'property_type': 'ประเภททรัพย์สิน',
            'address': 'ที่อยู่ทรัพย์สิน',
            'province': 'จังหวัด',
            'postal_code': 'รหัสไปรษณีย์',
            'estimated_value': 'มูลค่าประเมิน (บาท)',
            'purchase_price': 'ราคาซื้อ (บาท)',
            'purchase_date': 'วันที่ซื้อ',
            'land_size': 'ขนาดที่ดิน (ตร.ว.)',
            'building_size': 'ขนาดอาคาร (ตร.ม.)',
            'has_existing_loan': 'มีสินเชื่ออยู่',
            'existing_loan_balance': 'ยอดหนี้คงเหลือ (บาท)',
            'existing_bank': 'ธนาคารปัจจุบัน',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'province': forms.Select(attrs={'class': 'form-select'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'land_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'building_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'has_existing_loan': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'existing_loan_balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'existing_bank': forms.Select(attrs={'class': 'form-select'}),
        }


class LoanApplicationForm(forms.ModelForm):
    # แสดงเป็น checkbox (เลือกได้หลายธนาคาร)
    selected_banks = forms.ModelMultipleChoiceField(
        queryset=Bank.objects.filter(is_active=True).order_by('name'),
        required=True,
        label='เลือกธนาคารที่ต้องการยื่นคำขอ',
        widget=CheckboxSelectMultiple(attrs={'class': 'bank-checkbox form-check-input'})
    )

    class Meta:
        model = LoanApplication
        # ไม่ต้องใส่ ManyToManyField ของ model เช่น banks เพราะจัดการผ่าน selected_banks
        fields = [
            'property', 'loan_amount', 'loan_term', 'purpose',
            'monthly_income', 'monthly_expense', 'other_debts', 'notes'
        ]
        labels = {
            'property': 'เลือกทรัพย์สิน',
            'loan_amount': 'จำนวนเงินกู้ที่ต้องการ (บาท)',
            'loan_term': 'ระยะเวลากู้ (ปี)',
            'purpose': 'วัตถุประสงค์',
            'monthly_income': 'รายได้ต่อเดือน (บาท)',
            'monthly_expense': 'รายจ่ายต่อเดือน (บาท)',
            'other_debts': 'หนี้สินอื่น (บาท)',
            'notes': 'หมายเหตุ',
        }
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select', 'id': 'id_property'}),
            'loan_term': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_loan_term'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_purpose'}),
            'loan_amount': forms.TextInput(attrs={'class': 'form-control number-format', 'data-type': 'currency'}),
            'monthly_income': forms.TextInput(attrs={'class': 'form-control number-format', 'data-type': 'currency'}),
            'monthly_expense': forms.TextInput(attrs={'class': 'form-control number-format', 'data-type': 'currency'}),
            'other_debts': forms.TextInput(attrs={'class': 'form-control number-format', 'data-type': 'currency'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'id_notes'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # แสดงเฉพาะทรัพย์สินของผู้ใช้
        if user:
            self.fields['property'].queryset = Property.objects.filter(user=user)

        # ตั้งค่า default purpose
        if not self.initial.get('purpose'):
            self.initial['purpose'] = 'รีไฟแนนซ์สินเชื่อบ้าน'

        # ใส่ class เพิ่มให้ checkbox (ถ้าธีมต้องการ)
        self.fields['selected_banks'].widget.attrs.update({'class': 'bank-checkbox'})

    def clean_selected_banks(self):
        qs = self.cleaned_data.get('selected_banks')
        if not qs or qs.count() == 0:
            raise forms.ValidationError('กรุณาเลือกธนาคารอย่างน้อย 1 แห่ง')
        return qs



class LoanComparisonStep1Form(forms.Form):
    """ฟอร์มขั้นตอนที่ 1: ข้อมูลทรัพย์สินและสินเชื่อปัจจุบัน"""
    property_price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label='ราคาบ้าน/คอนโดที่ซื้อ (บาท)',
        min_value=Decimal('0.01'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5,000,000',
            'data-type': 'currency'
        })
    )

    current_loan_balance = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label='ยอดหนี้บ้านคงเหลือ (ไม่รวมยอดหนี้อื่นๆ) บาท',
        min_value=Decimal('0.01'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '3,000,000',
            'data-type': 'currency'
        })
    )

    current_monthly_payment = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label='ผ่อนต่อเดือน (หลังครบ 3 ปี ที่ธนาคารกำหนดไว้) บาท',
        required=False,
        min_value=Decimal('0.00'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '25,000',
            'data-type': 'currency'
        })
    )

    remaining_years = forms.ChoiceField(
        label='ต้องผ่อนอีกกี่ปี (ที่ธนาคารกำหนดไว้)',
        choices=REMAINING_YEARS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    current_bank = forms.ModelChoiceField(
        queryset=Bank.objects.filter(is_active=True),
        label='ธนาคารที่ผ่อนปัจจุบัน',
        empty_label='โปรดเลือกธนาคาร',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    need_extra_loan = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        label='ต้องการวงเงินกู้เพิ่มด้วยหรือไม่',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        property_price = cleaned_data.get('property_price')
        current_loan_balance = cleaned_data.get('current_loan_balance')

        if property_price and current_loan_balance:
            if current_loan_balance >= property_price:
                self.add_error('current_loan_balance', 'ยอดหนี้คงเหลือต้องน้อยกว่าราคาบ้าน/คอนโด')
        return cleaned_data

class LoanComparisonStep2Form(forms.Form):
    """ฟอร์มขั้นตอนที่ 2: ข้อมูลผู้กู้และอาชีพ"""

    occupation = forms.ChoiceField(
        choices=OCCUPATION_CHOICES,
        label='อาชีพปัจจุบัน',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    property_type = forms.ChoiceField(
        choices=PROPERTY_TYPE_CHOICES,
        label='ประเภทที่อยู่อาศัย',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    province = forms.ModelChoiceField(
        queryset=Province.objects.filter(is_active=True),
        label='จังหวัดของบ้านที่จะรีไฟแนนซ์',
        empty_label='โปรดเลือก',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        monthly_income = cleaned_data.get('monthly_income')

        if monthly_income is not None and monthly_income <= 0:
            self.add_error('monthly_income', "รายได้ต่อเดือนต้องมากกว่าศูนย์")

        return cleaned_data

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'document_type', 'file', 'description']
        labels = {
            'name': 'ชื่อเอกสาร',
            'document_type': 'ประเภทเอกสาร',
            'file': 'ไฟล์เอกสาร',
            'description': 'คำอธิบายเอกสาร',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# นี่คือ UserRegistrationForm ที่ถูกต้องและสมบูรณ์
class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='ชื่อจริง')
    last_name = forms.CharField(max_length=30, required=True, label='นามสกุล')
    email = forms.EmailField(required=True, label='อีเมล')
    
    phone_number_validator = RegexValidator(regex=r'^[0-9]{9,15}$', message="รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง (อนุญาตเฉพาะตัวเลข 9-15 หลัก)")
    phone_number = forms.CharField(
        max_length=15, 
        required=True, 
        label='เบอร์โทรศัพท์',
        validators=[phone_number_validator],
        help_text='ระบุเบอร์โทรศัพท์มือถือ 10 หลัก (เช่น 0812345678)'
    )

    terms_accepted = forms.BooleanField(
        required=True,
        label='คุณได้ยอมรับข้อตกลงและเงื่อนไข และนโยบายความเป็นส่วนตัว',
        error_messages={'required': 'กรุณาตรวจสอบว่าคุณได้ยอมรับข้อตกลงและเงื่อนไขแล้ว'}
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'terms_accepted')
        labels = {
            'username': 'ชื่อผู้ใช้ (สำหรับเข้าสู่ระบบ)',
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("อีเมลนี้ถูกใช้ไปแล้ว")
        return email
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("ชื่อผู้ใช้นี้ถูกใช้ไปแล้ว")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                terms_accepted=self.cleaned_data['terms_accepted']
            )
        return user
    
class ContactForm(forms.Form):
    """ฟอร์มติดต่อ"""
    name = forms.CharField(
        label='ชื่อ-นามสกุล',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='อีเมล',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label='เบอร์โทรศัพท์',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    subject = forms.CharField(
        label='หัวข้อ',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    message = forms.CharField(
        label='ข้อความ',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )


class BankFilterForm(forms.Form):
    """ฟอร์มกรองธนาคาร"""
    bank_type = forms.ChoiceField(
        label='ประเภทธนาคาร',
        choices=[('', 'ทั้งหมด')] + Bank.BANK_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    min_interest_rate = forms.DecimalField(
        label='อัตราดอกเบี้ยขั้นต่ำ (%)',
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    max_interest_rate = forms.DecimalField(
        label='อัตราดอกเบี้ยสูงสุด (%)',
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    min_loan_amount = forms.DecimalField(
        label='วงเงินกู้ขั้นต่ำ (บาท)',
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class PromotionFilterForm(forms.Form):
    """ฟอร์มกรองโปรโมชั่น"""
    bank = forms.ModelChoiceField(
        label='ธนาคาร',
        queryset=Bank.objects.filter(is_active=True),
        required=False,
        empty_label='ทุกธนาคาร',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    promotion_type = forms.ChoiceField(
        label='ประเภทโปรโมชั่น',
        choices=[('', 'ทั้งหมด')] + Promotion.PROMOTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_sponsored = forms.BooleanField(
        label='โปรโมชั่นสปอนเซอร์เท่านั้น',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        # เอาทุกฟิลด์ยกเว้น bank และ priority
        fields = [
            'title', 'description', 'promotion_type', 'min_loan_amount', 'max_loan_amount',
            'special_rate', 'special_rate_period', 'start_date', 'end_date',
            'is_active', 'is_sponsored', 'banner_image', 'terms_conditions'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'promotion_type': forms.Select(attrs={'class': 'form-select'}),
            'min_loan_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_loan_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'special_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'special_rate_period': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_sponsored': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'banner_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ใส่ค่า initial ให้ฟิลด์วันที่จาก instance
        if self.instance and self.instance.pk:
            if self.instance.start_date:
                self.fields['start_date'].initial = self.instance.start_date.strftime('%Y-%m-%d')
            if self.instance.end_date:
                self.fields['end_date'].initial = self.instance.end_date.strftime('%Y-%m-%d')

class LoanProductForm(forms.ModelForm):
    class Meta:
        model = LoanProduct
        # เลือกฟิลด์เองโดยเอา bank และ display_order ออก
        fields = [
            "name",
            "product_type",
            "description",
            "interest_rate",
            "interest_rate_type",
            "min_loan_amount",
            "max_loan_amount",
            "max_ltv",
            "max_term_years",
            "processing_fee",
            "appraisal_fee",
            "min_income",
            "min_age",
            "max_age",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "product_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "interest_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "interest_rate_type": forms.Select(attrs={"class": "form-select"}),
            "min_loan_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "max_loan_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "max_ltv": forms.NumberInput(attrs={"class": "form-control"}),
            "max_term_years": forms.NumberInput(attrs={"class": "form-control"}),
            "processing_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "appraisal_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "min_income": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "min_age": forms.NumberInput(attrs={"class": "form-control"}),
            "max_age": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ลบ label suffix
        for field in self.fields.values():
            field.label_suffix = ""

class QuickComparisonForm(forms.Form):
    """ฟอร์มเปรียบเทียบแบบเร็ว"""
    loan_amount = forms.DecimalField(
        label='จำนวนเงินกู้ (บาท)',
        max_digits=15,
        decimal_places=2,
        initial=3000000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3,000,000'
        })
    )

    loan_term = forms.IntegerField(
        label='ระยะเวลา (ปี)',
        min_value=5,
        max_value=30,
        initial=25,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '5',
            'max': '30'
        })
    )

    property_value = forms.DecimalField(
        label='มูลค่าทรัพย์สิน (บาท)',
        max_digits=15,
        decimal_places=2,
        initial=5000000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '5,000,000'
        })
    )

    employment_type = forms.ChoiceField(
        label='ประเภทอาชีพ',
        choices=[
            ('employee', 'พนักงานบริษัท'),
            ('government', 'ข้าราชการ'),
            ('business_owner', 'เจ้าของกิจการ'),
            ('other', 'อื่นๆ'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        loan_amount = cleaned_data.get('loan_amount')
        property_value = cleaned_data.get('property_value')

        if loan_amount and property_value:
            ltv = (loan_amount / property_value) * 100
            if ltv > 95:
                raise forms.ValidationError(
                    'สัดส่วนเงินกู้ต่อมูลค่าทรัพย์สิน (LTV) ไม่ควรเกิน 95%'
                )

        return cleaned_data


class NewsletterSubscriptionForm(forms.Form):
    """ฟอร์มสมัครรับข่าวสาร"""
    email = forms.EmailField(
        label='อีเมล',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )

    name = forms.CharField(
        label='ชื่อ',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ชื่อของคุณ'
        })
    )

    interests = forms.MultipleChoiceField(
        label='สนใจข่าวสารเกี่ยวกับ',
        choices=[
            ('interest_rates', 'อัตราดอกเบี้ย'),
            ('promotions', 'โปรโมชั่นพิเศษ'),
            ('tips', 'เทคนิคการเงิน'),
            ('news', 'ข่าวสารทั่วไป'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )


class FeedbackForm(forms.Form):
    """ฟอร์มความคิดเห็น"""
    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ ดีมาก'),
        (4, '⭐⭐⭐⭐ ดี'),
        (3, '⭐⭐⭐ ปานกลาง'),
        (2, '⭐⭐ พอใช้'),
        (1, '⭐ ต้องปรับปรุง'),
    ]

    rating = forms.ChoiceField(
        label='ความพึงพอใจโดยรวม',
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    feedback = forms.CharField(
        label='ความคิดเห็นและข้อเสนอแนะ',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'แบ่งปันความคิดเห็นของคุณ...'
        })
    )

    recommend = forms.BooleanField(
        label='จะแนะนำบริการนี้ให้เพื่อนหรือไม่',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    contact_email = forms.EmailField(
        label='อีเมลติดต่อกลับ (ถ้าต้องการ)',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'citizen_id', 'date_of_birth', 'address', 
                 'income_source', 'monthly_income', 'monthly_expenses'] # สลับ profile_picture ขึ้นมา
        labels = {
            'profile_picture': 'รูปโปรไฟล์',
            'phone_number': 'เบอร์โทรศัพท์',
            'citizen_id': 'เลขบัตรประชาชน',
            'date_of_birth': 'วันเกิด',
            'address': 'ที่อยู่',
            'income_source': 'แหล่งรายได้',
            'monthly_income': 'รายได้ต่อเดือน (บาท)',
            'monthly_expenses': 'รายจ่ายต่อเดือน (บาท)',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0812345678'}),
            'citizen_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '13 หลัก'}),
            'monthly_income': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'monthly_expenses': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'income_source': forms.Select(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}) # ให้เป็น file input
        }


## **โค้ด `refinance/forms.py` (แก้ไขแล้ว)**


