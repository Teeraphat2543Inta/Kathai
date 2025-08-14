# kathai_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # App URLs - ระวังลำดับ! dashboard ต้องมาก่อน refinance เพราะใช้ path('')
    path('dashboard/', include('dashboard.urls')),  # dashboard URLs ต้องระบุ path เฉพาะ
    path('accounts/', include('accounts.urls')),    # accounts URLs
    path('', include('refinance.urls')),            # refinance เป็น main app (มาท้ายสุด)
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)