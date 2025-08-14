# dashboard/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from refinance.models import LoanApplication, Property, ApplicationBank # ต้องแน่ใจว่า import ถูกต้อง

# @login_required
def dashboard_home(request): # ลบ @login_required ชั่วคราวเพื่อทดสอบ template ได้ง่ายขึ้น แต่ต้องใส่กลับเมื่อใช้งานจริง
    # สถิติของผู้ใช้
    user = request.user # ดึง user object มาใช้งาน
    user_stats = {
        'total_applications': LoanApplication.objects.filter(user=user).count(), # แก้จาก applicant เป็น user
        'pending_applications': LoanApplication.objects.filter( 
            user=user, status__in=['pending', 'submitted', 'under_review'] # แก้จาก applicant เป็น user. ตรวจสอบ status ที่ถูกต้องใน LoanApplication model ของคุณ
        ).count(),
        'approved_applications': LoanApplication.objects.filter( 
            user=user, status='approved' # แก้จาก applicant เป็น user
        ).count(),
        'total_properties': Property.objects.filter(user=user).count(), # แก้จาก owner เป็น user
    }

    # คำขอล่าสุด
    recent_applications = LoanApplication.objects.filter( 
        user=user # แก้จาก applicant เป็น user
    ).order_by('-submitted_at')[:5] # แก้จาก -application_date เป็น -submitted_at หรือ -created_at

    # ทรัพย์สินของผู้ใช้
    user_properties = Property.objects.filter(user=user)[:3] # แก้จาก owner เป็น user

    context = {
        'user_stats': user_stats,
        'recent_applications': recent_applications,
        'user_properties': user_properties,
    }

    return render(request, 'dashboard/home.html', context)

# @login_required
def application_tracking(request): # ลบ @login_required ชั่วคราว
    user = request.user # ดึง user object มาใช้งาน
    applications = LoanApplication.objects.filter( 
        user=user # แก้จาก applicant เป็น user
    ).prefetch_related('applicationbank_set__bank__loanproduct_set') 

    return render(request, 'dashboard/application_tracking.html', {
        'applications': applications
    })