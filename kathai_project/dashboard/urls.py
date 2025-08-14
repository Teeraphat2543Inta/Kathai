# dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home URL
    path('', views.dashboard_home, name='home'),
    # aliases
    path('home/', views.dashboard_home, name='dashboard'),
    path('overview/', views.dashboard_home, name='overview'),
    
    # URLs อื่นๆ ของ dashboard (ถ้ามี)
    # path('stats/', views.dashboard_stats, name='stats'),
    # path('reports/', views.dashboard_reports, name='reports'),
]