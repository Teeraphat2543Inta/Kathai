from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm
from .models import UserProfile, User # ตรวจสอบให้แน่ใจว่า import User ด้วย

def home(request):
    return render(request, 'home.html') 


from django.shortcuts import render, redirect
from django.contrib import messages

from accounts.models import UserProfile

# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from refinance.forms import UserRegistrationForm # <-- ตรวจสอบว่ามีการ import ถูกต้องแล้ว

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')

def terms_and_conditions(request):
    return render(request, 'accounts/terms_and_conditions.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'ลงทะเบียนสำเร็จ! คุณสามารถเข้าสู่ระบบและกรอกข้อมูลส่วนตัวเพิ่มเติมได้')
            return redirect('accounts:profile_setup') # หรือหน้าที่คุณต้องการให้ไปต่อ
        else:
            # การแสดงข้อความผิดพลาดที่ละเอียดขึ้น
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_setup(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user) 

    if request.method == 'POST':
        # ตรวจสอบให้แน่ใจว่า request.FILES ถูกส่งไปด้วย
        form = UserProfileForm(request.POST, request.FILES, instance=profile) 
        if form.is_valid():
            form.save()
            messages.success(request, 'บันทึกข้อมูลส่วนตัวเรียบร้อย')
            return redirect('dashboard:home') 
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/profile_setup.html', {'form': form})

@login_required
def profile_edit(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.warning(request, 'กรุณาตั้งค่าโปรไฟล์ของคุณก่อน')
        return redirect('accounts:profile_setup')

    if request.method == 'POST':
        # ตรวจสอบให้แน่ใจว่า request.FILES ถูกส่งไปด้วย
        form = UserProfileForm(request.POST, request.FILES, instance=profile) 
        if form.is_valid():
            form.save()
            messages.success(request, 'อัปเดตข้อมูลเรียบร้อย')
            return redirect('dashboard:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})