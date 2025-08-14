from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# ตรวจสอบให้แน่ใจว่าได้นำเข้า UserProfile จาก accounts.models อย่างถูกต้อง
# เช่น: from accounts.models import UserProfile
# หาก UserProfile อยู่ในแอปอื่น (เช่น refinance) ให้เปลี่ยน path ให้ถูกต้อง
# ตัวอย่าง: from refinance.models import UserProfile
from accounts.models import UserProfile 

class UserRegistrationForm(UserCreationForm):
    """
    ฟอร์มสำหรับลงทะเบียนผู้ใช้งานใหม่
    สืบทอดจาก UserCreationForm ของ Django เพื่อจัดการการสร้าง User
    และเพิ่มฟิลด์สำหรับข้อมูลส่วนตัวเพิ่มเติม เช่น ชื่อ, นามสกุล, อีเมล, เบอร์โทรศัพท์ และการยอมรับเงื่อนไข
    """
    first_name = forms.CharField(max_length=30, required=True, label='ชื่อจริง')
    last_name = forms.CharField(max_length=30, required=True, label='นามสกุล')
    email = forms.EmailField(required=True, label='อีเมล')
    
    # กำหนด validator สำหรับเบอร์โทรศัพท์ เพื่อให้แน่ใจว่าเป็นตัวเลข 9-15 หลัก
    phone_number_validator = RegexValidator(regex=r'^[0-9]{9,15}$', 
                                            message="รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง (อนุญาตเฉพาะตัวเลข 9-15 หลัก)")
    phone_number = forms.CharField(
        max_length=15, 
        required=True, 
        label='เบอร์โทรศัพท์',
        validators=[phone_number_validator],
        help_text='ระบุเบอร์โทรศัพท์มือถือ 10 หลัก (เช่น 0812345678)'
    )

    # ฟิลด์สำหรับยอมรับข้อตกลงและเงื่อนไข (บังคับให้ต้องเลือก)
    terms_accepted = forms.BooleanField(
        required=True,
        label='คุณได้ยอมรับข้อตกลงและเงื่อนไข และนโยบายความเป็นส่วนตัว',
        error_messages={'required': 'กรุณาตรวจสอบว่าคุณได้ยอมรับข้อตกลงและเงื่อนไขแล้ว'}
    )

    class Meta(UserCreationForm.Meta):
        """
        Meta class สำหรับ UserRegistrationForm
        กำหนดโมเดลที่ใช้ (User) และฟิลด์ที่ต้องการให้แสดงในฟอร์ม
        """
        model = User
        # เพิ่มฟิลด์ที่กำหนดเองเข้าไปใน fields ของ UserCreationForm
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'terms_accepted')
        labels = {
            'username': 'ชื่อผู้ใช้ (สำหรับเข้าสู่ระบบ)',
        }

    def clean_email(self):
        """
        ตรวจสอบความถูกต้องของอีเมล: ห้ามใช้อีเมลซ้ำ
        """
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("อีเมลนี้ถูกใช้ไปแล้ว")
        return email
    
    def clean_username(self):
        """
        ตรวจสอบความถูกต้องของชื่อผู้ใช้: ห้ามใช้ชื่อผู้ใช้ซ้ำ
        """
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("ชื่อผู้ใช้นี้ถูกใช้ไปแล้ว")
        return username

    def save(self, commit=True):
        """
        บันทึกข้อมูลผู้ใช้งานและสร้าง UserProfile
        """
        # บันทึก User (username, password) โดยยังไม่ commit ลงฐานข้อมูล
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            # บันทึก User ลงฐานข้อมูล
            user.save()
            # สร้าง UserProfile และบันทึกข้อมูลเพิ่มเติม
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                terms_accepted=self.cleaned_data['terms_accepted'] # บันทึกค่าการยอมรับเงื่อนไข
            )
        return user
    
class UserProfileForm(forms.ModelForm):
    """
    ฟอร์มสำหรับแก้ไขหรืออัปเดตข้อมูล UserProfile ของผู้ใช้งาน
    """
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'citizen_id', 'date_of_birth', 'address', 
                 'income_source', 'monthly_income', 'monthly_expenses'] 
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
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}) 
        }

