# kathai_project/middleware.py
from django.utils.deprecation import MiddlewareMixin
from accounts.models import ActivityLog # ตรวจสอบให้แน่ใจว่า import ถูกต้องจาก accounts.models
import json # สำหรับการจัดการ JSON

class ActivityLogMiddleware(MiddlewareMixin):
    """Middleware สำหรับบันทึก Activity Log ของผู้ใช้"""
    
    def process_response(self, request, response):
        # บันทึกเฉพาะ GET requests ที่สำคัญ
        if request.method == 'GET' and response.status_code == 200:
            self.log_page_view(request)
        
        # เพิ่มการบันทึก POST requests ที่สำเร็จ
        elif request.method == 'POST' and response.status_code == 200:
            self.log_form_submission(request)

        return response
    
    def log_page_view(self, request):
        """บันทึกการดูหน้าเว็บ"""
        try:
            # ไม่บันทึก admin, static files, และ AJAX requests
            if any(skip in request.path for skip in ['/admin/', '/static/', '/media/', 'ajax']):
                return
            
            # ไม่บันทึกถ้ามี X-Requested-With header (AJAX)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return
            
            user = request.user if request.user.is_authenticated else None
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # สร้างคำอธิบาย
            page_map = {
                '/': 'หน้าแรก',
                '/accounts/login/': 'หน้าเข้าสู่ระบบ', # แก้ไข path ให้ตรงกับ urls
                '/accounts/register/': 'หน้าสมัครสมาชิก', # แก้ไข path ให้ตรงกับ urls
                '/dashboard/home/': 'แดชบอร์ด', # แก้ไข path ให้ตรงกับ urls
                '/refinance/comparison/': 'เปรียบเทียบดอกเบี้ย',
                '/refinance/property/': 'รายการทรัพย์สิน',
                '/refinance/application/': 'รายการคำขอ',
                '/accounts/profile/setup/': 'ตั้งค่าโปรไฟล์', # เพิ่ม path
                '/accounts/profile/edit/': 'แก้ไขโปรไฟล์', # เพิ่ม path
            }
            
            description = page_map.get(request.path, f'เข้าชมหน้า: {request.path}')
            
            ActivityLog.objects.create(
                user=user,
                activity_type='page_view',
                description=description,
                url=request.path,
                ip_address=ip_address,
                user_agent=user_agent[:500],  # จำกัดความยาว
                session_key=request.session.session_key or '',
                extra_data={
                    'method': request.method,
                    'referer': request.META.get('HTTP_REFERER', ''),
                }
            )
        except Exception as e:
            # ไม่ให้ error ใน logging ทำให้ระบบล่ม
            print(f"Error logging page view: {e}") # พิมพ์ error เพื่อ debug
            pass

    def log_form_submission(self, request):
        """บันทึกการส่งฟอร์ม (POST requests)"""
        try:
            if any(skip in request.path for skip in ['/admin/', '/static/', '/media/', 'ajax']):
                return
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return

            user = request.user if request.user.is_authenticated else None
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # พยายามดึงข้อมูลที่ส่งมาในฟอร์ม (ระวังข้อมูล sensitive)
            post_data = {k: v for k, v in request.POST.items() if 'password' not in k.lower()} # ไม่บันทึก password
            
            description = f"ส่งฟอร์มที่: {request.path}"
            
            ActivityLog.objects.create(
                user=user,
                activity_type='form_submission',
                description=description,
                url=request.path,
                ip_address=ip_address,
                user_agent=user_agent[:500],
                session_key=request.session.session_key or '',
                extra_data={
                    'method': request.method,
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'post_data_preview': str(post_data)[:500] # บันทึกแค่บางส่วน
                }
            )
        except Exception as e:
            print(f"Error logging form submission: {e}")
            pass
    
    def get_client_ip(self, request):
        """ดึง IP address ของผู้ใช้"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# ฟังก์ชันสำหรับบันทึก activity แบบ manual (ถ้าต้องการเรียกใช้จาก view หรือส่วนอื่น)
def log_activity(user, activity_type, description, request=None, **extra_data):
    """ฟังก์ชันสำหรับบันทึก activity แบบ manual"""
    ip_address = None
    user_agent = ''
    session_key = ''
    
    if request:
        middleware_instance = ActivityLogMiddleware(lambda r: None) # สร้าง instance ชั่วคราว
        ip_address = middleware_instance.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        session_key = request.session.session_key or ''
    
    ActivityLog.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent[:500],
        session_key=session_key,
        extra_data=extra_data
    )