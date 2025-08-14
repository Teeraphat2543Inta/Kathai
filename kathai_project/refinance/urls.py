# refinance/urls.py

from django.urls import path
from . import views
from .views import LoanComparisonWizard, FORMS

app_name = 'refinance'

urlpatterns = [
    # URLs สำหรับหน้าแรก (home)
    path('', views.home, name='home'),
    

    # --- URLs สำหรับ Property ---
    path('properties/add/', views.property_create, name='property_create'),
    # เพิ่ม aliases สำหรับ template ที่อาจใช้ชื่ออื่น
    path('properties/new/', views.property_create, name='property_add'),
    path('properties/create/', views.property_create, name='property_new'),
    path('property/add/', views.property_add, name='property_add'),
    path('faq/', views.faq_view, name='faq'),
    path('articles/', views.article_list_view, name='article_list'),
    path('articles/<slug:slug>/', views.article_detail_view, name='article_detail'),
    
    path('properties/', views.property_list, name='property_list'),
    path('properties/<int:pk>/', views.property_detail, name='property_detail'),
    path('properties/<int:pk>/edit/', views.property_update, name='property_update'),
    path('properties/<int:pk>/delete/', views.property_delete, name='property_delete'),

    # --- URLs สำหรับ Loan Application ---
    path('applications/create/', views.loan_application_create, name='loan_application_create'),
    # เพิ่ม alias สำหรับ template
    path('applications/new/', views.loan_application_create, name='application_create'),
    path('applications/add/', views.loan_application_create, name='application_add'),
    
    path('applications/', views.loan_application_list, name='loan_application_list'),
    # เพิ่ม alias สำหรับ template ที่ใช้ชื่อเดิม
    path('applications/list/', views.loan_application_list, name='application_list'),
    
    path('applications/<int:pk>/', views.loan_application_detail, name='loan_application_detail'),
    # เพิ่ม alias
    path('applications/<int:pk>/view/', views.loan_application_detail, name='application_detail'),
    
    path('applications/<int:pk>/update/', views.loan_application_update, name='loan_application_update'),
    # เพิ่ม alias
    path('applications/<int:pk>/edit/', views.loan_application_update, name='application_update'),
    
    # ใน refinance/urls.py ควรมี
    path('applications/<int:pk>/submit/', views.loan_application_submit, name='loan_application_submit'),
    # เพิ่ม alias
    path('applications/<int:pk>/send/', views.loan_application_submit, name='application_submit'),
    
    path('applications/<int:pk>/delete/', views.loan_application_delete, name='loan_application_delete'),
    # เพิ่ม alias
    path('applications/<int:pk>/remove/', views.loan_application_delete, name='application_delete'),

    path('applications/<int:application_pk>/documents/upload/', views.document_upload, name='document_upload_for_application'),

    # --- URLs สำหรับ Document ---
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    # เพิ่ม alias
    path('documents/add/', views.document_upload, name='document_add'),
    path('documents/new/', views.document_upload, name='document_new'),
    
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),

    # --- URLs สำหรับ Loan Comparison Wizard (Multi-step Form) ---
    path('compare/', LoanComparisonWizard.as_view(FORMS), name='loan_comparison_wizard'),
    # เพิ่ม alias
    path('comparison/', LoanComparisonWizard.as_view(FORMS), name='loan_comparison'),
    path('compare-loans/', LoanComparisonWizard.as_view(FORMS), name='compare_loans'),

    # --- URLs สำหรับหน้าเปรียบเทียบแบบ Quick Comparison (ถ้ามี) ---
    path('quick-compare/', views.refinance_comparison_form, name='refinance_comparison_form'),

    # --- เพิ่มบรรทัดนี้สำหรับหน้าแสดงผลการเปรียบเทียบสินเชื่อเริ่มต้น ---
    # บรรทัดนี้จะแก้ปัญหา NoReverseMatch ที่คุณเจอ
    # อย่าลืมเปลี่ยน 'views.your_loan_comparison_results_view' ให้เป็นชื่อฟังก์ชัน/คลาส View จริงๆ ของคุณ
    # ที่ใช้สำหรับแสดงผลหน้า 'loan_comparison_results.html'
    path('loan-comparison-results/', views.loan_comparison_results_view, name='loan_comparison_results'),
    # ------------------------------------------------------------------

    # --- URLs สำหรับหน้าแดชบอร์ด ---
    path('dashboard/', views.dashboard_view, name='dashboard'),
    # เพิ่ม alias
    path('my-dashboard/', views.dashboard_view, name='user_dashboard'),
    
    # --- URLs สำหรับ Bank และ Loan Product ---
    path('banks/', views.bank_list, name='bank_list'),
    path('banks/<int:pk>/', views.bank_detail, name='bank_detail'),
    path('loan-products/', views.loan_product_list, name='loan_product_list'),
    path('loan-products/<int:pk>/', views.loan_product_detail, name='loan_product_detail'),

    # --- URLs สำหรับ Contact Us ---
    path('contact/', views.contact_us, name='contact_us'),
    # เพิ่ม alias
    path('contact-us/', views.contact_us, name='contact'),

    # --- URLs สำหรับ API endpoints ---
    path('api/banks/search/', views.search_banks_api, name='api_search_banks'),
    path('api/loan-products/search/', views.search_loan_products_api, name='api_search_loan_products'),
    
    
    path('applications/tracking/', views.loan_application_list, name='application_tracking'),
    path('tracking/', views.loan_application_list, name='tracking'),  # alias อีกตัว
    
     # *** มีอยู่แล้วในไฟล์ของคุณ ***
    path('loan-summary-comparison/', views.loan_summary_comparison_view, name='loan_summary_comparison'),
    path('apply/<int:product_id>/', views.apply_loan, name='apply_loan'),
    path('api/properties/<int:property_id>/', views.get_property_details_api, name='api_get_property_details'),
    path('api/loan_products_by_property/<int:property_id>/', views.get_loan_products_by_property_api, name='api_get_loan_products_by_property'),
    path('promotions/', views.advertisement_list_view, name='advertisement_list'),
   

    
    
]