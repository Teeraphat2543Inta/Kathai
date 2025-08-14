# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html # สำหรับแสดงผล JSONField
from .models import UserProfile, ActivityLog # เพิ่ม ActivityLog ที่นี่
import json # สำหรับ pretty print JSON

# Define an inline admin descriptor for UserProfile model
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'ข้อมูลโปรไฟล์เพิ่มเติม'
    fields = (
        ('phone_number', 'citizen_id'),
        ('date_of_birth', 'profile_picture'),
        'address',
        ('income_source', 'monthly_income', 'monthly_expenses'),
    )
    readonly_fields = ['created_at', 'updated_at']

# เพิ่ม Inline สำหรับ ActivityLog
class ActivityLogInline(admin.TabularInline):
    model = ActivityLog
    can_delete = False
    extra = 0
    verbose_name_plural = 'บันทึกการใช้งานล่าสุด'
    # เพิ่มฟิลด์ใหม่ๆ ที่จะแสดงในตาราง
    fields = ('activity_type', 'description', 'url', 'timestamp', 'ip_address', 'user_agent_preview', 'session_key', 'extra_data_preview')
    # กำหนดให้ฟิลด์เหล่านี้เป็น readonly
    readonly_fields = ('activity_type', 'description', 'url', 'timestamp', 'ip_address', 'user_agent_preview', 'session_key', 'extra_data_preview')

    @admin.display(description='User Agent (Preview)')
    def user_agent_preview(self, obj):
        return obj.user_agent[:100] + '...' if obj.user_agent and len(obj.user_agent) > 100 else obj.user_agent

    @admin.display(description='ข้อมูลเพิ่มเติม')
    def extra_data_preview(self, obj):
        if obj.extra_data:
            # แสดง JSON แบบสวยงาม
            pretty_json = json.dumps(obj.extra_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 150px; overflow-y: auto; background-color: #f8f8f8; padding: 5px; border-radius: 3px;">{}</pre>', pretty_json)
        return '-'

# Extend UserAdmin to include UserProfileInline and ActivityLogInline
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, ActivityLogInline,) # <--- เพิ่ม ActivityLogInline ที่นี่

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('ข้อมูลส่วนตัว', {'fields': ('first_name', 'last_name', 'email')}),
        ('สิทธิ์การใช้งาน', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('ข้อมูลเวลา', {'fields': ('last_login', 'date_joined')}),
    )

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'get_phone_number',
        'get_citizen_id',
        'get_profile_status'
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'userprofile__phone_number',
        'userprofile__citizen_id'
    )
    list_filter = BaseUserAdmin.list_filter + ('userprofile__income_source', 'userprofile__created_at')

    @admin.display(description='เบอร์โทรศัพท์')
    def get_phone_number(self, obj):
        return obj.userprofile.phone_number if hasattr(obj, 'userprofile') else '-'

    @admin.display(description='เลขบัตรประชาชน')
    def get_citizen_id(self, obj):
        return obj.userprofile.citizen_id if hasattr(obj, 'userprofile') else '-'

    @admin.display(description='สถานะโปรไฟล์')
    def get_profile_status(self, obj):
        if hasattr(obj, 'userprofile'):
            profile = obj.userprofile
            required_fields = ['phone_number', 'citizen_id', 'date_of_birth', 'address', 'income_source', 'monthly_income', 'monthly_expenses']
            filled_fields = [f for f in required_fields if getattr(profile, f)]
            if len(filled_fields) == len(required_fields):
                return 'สมบูรณ์'
            elif len(filled_fields) > 0:
                return 'ข้อมูลบางส่วน'
            else:
                return 'ยังไม่มีข้อมูล'
        return 'ไม่มีโปรไฟล์'
    get_profile_status.admin_order_field = 'userprofile__phone_number'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# ลงทะเบียน ActivityLog เป็นโมเดลแยกต่างหากใน Admin (ถ้าต้องการดู Log ทั้งหมด)
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'description', 'url', 'timestamp', 'ip_address', 'user_agent_preview']
    list_filter = ['activity_type', 'timestamp', 'user']
    search_fields = ['user__username', 'activity_type', 'description', 'url', 'ip_address']
    readonly_fields = ['user', 'activity_type', 'description', 'url', 'timestamp', 'ip_address', 'user_agent', 'session_key', 'extra_data']

    @admin.display(description='User Agent (Preview)')
    def user_agent_preview(self, obj):
        return obj.user_agent[:100] + '...' if obj.user_agent and len(obj.user_agent) > 100 else obj.user_agent