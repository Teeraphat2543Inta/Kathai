# your_project_name/urls.py (ไฟล์หลักของโปรเจกต์)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views # บรรทัดนี้คือสิ่งสำคัญ

app_name = 'accounts'

urlpatterns = [
    # Home URL
    path('', views.home, name='home'),
    
    # Login/Logout URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Registration URLs
    path('register/', views.register, name='register'),
    path('signup/', views.register, name='signup'),  # alias
    
    # Profile URLs
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    # aliases สำหรับ template ที่อาจใช้ชื่ออื่น
    path('profile/', views.profile_edit, name='profile'),
    path('profile/update/', views.profile_edit, name='profile_update'),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
    
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
]

# สำคัญมาก: เพิ่มบรรทัดนี้สำหรับการพัฒนาเพื่อเสิร์ฟ media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)