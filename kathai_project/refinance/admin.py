from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from decimal import Decimal
import statistics
from django.utils import timezone

from .models import (
    Province, Bank, LoanProduct, Promotion, FeeType, Fee,
    Property, LoanApplication, ApplicationBank, Document,
    ActivityLog, SystemSetting, InterestRateHistory,
    Advertisement, Article
)

# Custom admin site configuration
admin.site.site_header = "KATHAI - ระบบจัดการข้อมูลธนาคาร"
admin.site.site_title = "KATHAI Admin"
admin.site.index_title = "ระบบจัดการข้อมูลธนาคารและสินเชื่อ"


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_date', 'slug', 'is_published')
    list_filter = ('published_date',)
    search_fields = ('title', 'content')
    date_hierarchy = 'published_date'
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('ข้อมูลบทความ', {
            'fields': ('title', 'slug', 'summary', 'content', 'image')
        }),
        ('วันที่เผยแพร่', {
            'fields': ('published_date',)
        }),
    )

    def is_published(self, obj):
        return format_html('<span style="color: {};">● {}</span>',
                           '#4caf50' if obj.published_date <= timezone.now() else '#ff9800',
                           'เผยแพร่แล้ว' if obj.published_date <= timezone.now() else 'รอเผยแพร่')
    is_published.short_description = 'สถานะ'


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'region', 'is_active', 'display_order']
    list_filter = ['region', 'is_active']
    search_fields = ['name', 'name_en']
    ordering = ['display_order', 'name']
    list_editable = ['is_active', 'display_order']


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'bank_type', 'colored_brand',
        'logo_preview',
        'is_featured',
        'is_active', 'loan_products_count', 'promotions_count', 'display_order'
    ]
    list_filter = ['bank_type', 'is_featured', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['display_order', 'name']
    list_editable = ['is_featured', 'is_active', 'display_order']

    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('name', 'code', 'bank_type', 'description')
        }),
        ('การตั้งค่าการแสดงผล', {
            'fields': ('brand_color', 'logo', 'is_featured', 'is_active', 'display_order')
        }),
        ('ข้อมูลติดต่อ', {
            'fields': ('website', 'contact_phone', 'contact_email')
        }),
        ('การตลาด', {
            'fields': ('marketing_message',),
            'classes': ('collapse',)
        }),
    )

    def colored_brand(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            obj.brand_color,
            obj.brand_color
        )
    colored_brand.short_description = 'สีแบรนด์'

    def logo_preview(self, obj):
        if obj.logo and hasattr(obj.logo, 'url'):
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.logo.url)
        return "-"
    logo_preview.short_description = 'โลโก้'

    def loan_products_count(self, obj):
        count = obj.loan_products.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:refinance_loanproduct_changelist')
            return format_html(
                '<a href="{}?bank__id__exact={}">{} ผลิตภัณฑ์</a>',
                url, obj.pk, count
            )
        return "0 ผลิตภัณฑ์"
    loan_products_count.short_description = 'ผลิตภัณฑ์'

    def promotions_count(self, obj):
        count = obj.promotions.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:refinance_promotion_changelist')
            return format_html(
                '<a href="{}?bank__id__exact={}">{} โปรโมชั่น</a>',
                url, obj.pk, count
            )
        return "0 โปรโมชั่น"
    promotions_count.short_description = 'โปรโมชั่น'


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'bank', 'product_type', 'interest_rate_display',
        'loan_range', 'max_ltv', 'max_term_years', 'is_active', 'is_popular'
    ]
    list_filter = [
        'product_type', 'bank__bank_type', 'is_active', 'is_popular',
        'bank', 'interest_rate_type'
    ]
    search_fields = ['name', 'bank__name']
    ordering = ['bank__name', 'display_order', 'name']
    list_editable = ['is_active', 'is_popular']

    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('bank', 'name', 'product_type', 'description')
        }),
        ('อัตราดอกเบี้ย', {
            'fields': ('interest_rate', 'interest_rate_type')
        }),
        ('วงเงินและเงื่อนไข', {
            'fields': (
                ('min_loan_amount', 'max_loan_amount'),
                ('max_ltv', 'max_term_years'),
                ('min_income', 'min_age', 'max_age')
            )
        }),
        ('ค่าธรรมเนียม', {
            'fields': ('processing_fee', 'appraisal_fee')
        }),
        ('การตั้งค่า', {
            'fields': ('is_active', 'is_popular', 'display_order')
        }),
    )

    def interest_rate_display(self, obj):
        color = '#4caf50' if obj.interest_rate < Decimal('3.0') else '#ff9800' if obj.interest_rate < Decimal('3.5') else '#f44336'
        formatted_rate = f"{obj.interest_rate:.2f}%"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, formatted_rate
        )
    interest_rate_display.short_description = 'อัตราดอกเบี้ย'

    def loan_range(self, obj):
        return f'{obj.min_loan_amount:,.0f} - {obj.max_loan_amount:,.0f}'
    loan_range.short_description = 'วงเงินกู้ (บาท)'

    actions = ['update_rates_action']

    def update_rates_action(self, request, queryset):
        pass
    update_rates_action.short_description = "อัปเดตอัตราดอกเบี้ย"


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'bank', 'promotion_type', 'special_rate_display',
        'date_range', 'status_display', 'priority', 'is_sponsored'
    ]
    list_filter = [
        'promotion_type', 'is_active', 'is_sponsored', 'bank',
        'start_date', 'end_date'
    ]
    search_fields = ['title', 'bank__name', 'description']
    ordering = ['-is_sponsored', '-priority', '-start_date']
    list_editable = ['priority', 'is_sponsored']

    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('bank', 'title', 'description', 'promotion_type')
        }),
        ('เงื่อนไขโปรโมชั่น', {
            'fields': (
                ('min_loan_amount', 'max_loan_amount'),
                ('special_rate', 'special_rate_period')
            )
        }),
        ('ระยะเวลา', {
            'fields': ('start_date', 'end_date')
        }),
        ('การตั้งค่า', {
            'fields': ('is_active', 'is_sponsored', 'priority')
        }),
        ('ข้อกำหนด', {
            'fields': ('terms_conditions',),
            'classes': ('collapse',)
        }),
        ('สื่อการตลาด', {
            'fields': ('banner_image',),
            'classes': ('collapse',)
        }),
    )

    def special_rate_display(self, obj):
        if obj.special_rate:
            formatted_special_rate = f"{obj.special_rate:.2f}%"
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">{}</span> '
                '<small>({} เดือน)</small>',
                formatted_special_rate, obj.special_rate_period or 12
            )
        return '-'
    special_rate_display.short_description = 'อัตราพิเศษ'

    def date_range(self, obj):
        return f'{obj.start_date.strftime("%d/%m")} - {obj.end_date.strftime("%d/%m/%Y")}'
    date_range.short_description = 'ระยะเวลา'

    def status_display(self, obj):
        if obj.is_valid_now():
            return format_html('<span style="color: #4caf50;">● ใช้งานได้</span>')
        elif obj.is_active:
            return format_html('<span style="color: #ff9800;">● รอเริ่มใช้งาน</span>')
        else:
            return format_html('<span style="color: #f44336;">● ปิดใช้งาน</span>')
    status_display.short_description = 'สถานะ'


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'fee_type', 'is_active']
    list_filter = ['fee_type', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = [
        'bank', 'fee_type', 'amount_display', 'range_display', 'is_active'
    ]
    list_filter = ['fee_type', 'bank', 'is_active']
    search_fields = ['bank__name', 'fee_type__name']
    ordering = ['bank__name', 'fee_type__name']

    def amount_display(self, obj):
        if obj.fee_type.fee_type == 'percentage':
            return f'{obj.amount}%'
        else:
            return f'{obj.amount:,.0f} บาท'
    amount_display.short_description = 'จำนวน'

    def range_display(self, obj):
        if obj.min_amount or obj.max_amount:
            min_val = f'{obj.min_amount:,.0f}' if obj.min_amount else '0'
            max_val = f'{obj.max_amount:,.0f}' if obj.max_amount else '∞'
            return f'{min_val} - {max_val} บาท'
        return '-'
    range_display.short_description = 'ช่วงจำนวน'


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'property_type', 'province', 'estimated_value_display',
        'has_existing_loan', 'created_at'
    ]
    list_filter = [
        'property_type', 'province', 'has_existing_loan', 'created_at'
    ]
    search_fields = ['name', 'user__username', 'address']
    ordering = ['-created_at']

    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('user', 'name', 'property_type')
        }),
        ('ที่อยู่', {
            'fields': ('address', 'province', 'postal_code')
        }),
        ('มูลค่าและการประเมิน', {
            'fields': (
                ('estimated_value', 'purchase_price'),
                'purchase_date'
            )
        }),
        ('ขนาด', {
            'fields': ('land_size', 'building_size'),
            'classes': ('collapse',)
        }),
        ('สินเชื่อปัจจุบัน', {
            'fields': ('has_existing_loan', 'existing_loan_balance', 'existing_bank')
        }),
    )

    def estimated_value_display(self, obj):
        return f'{obj.estimated_value:,.0f} บาท'
    estimated_value_display.short_description = 'มูลค่าประเมิน'


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'application_no', 'user', 'property', 'loan_amount_display',
        'status_display', 'submitted_at', 'banks_count'
    ]
    list_filter = ['status', 'submitted_at', 'created_at']
    search_fields = ['application_no', 'user__username', 'property__name']
    ordering = ['-created_at']
    readonly_fields = ['application_no', 'created_at', 'updated_at']

    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('user', 'application_no', 'property')
        }),
        ('ข้อมูลสินเชื่อ', {
            'fields': ('loan_amount', 'loan_term', 'purpose')
        }),
        ('ข้อมูลทางการเงิน', {
            'fields': ('monthly_income', 'monthly_expense', 'other_debts')
        }),
        ('สถานะและการติดตาม', {
            'fields': ('status', 'submitted_at', 'reviewed_at', 'approved_at')
        }),
        ('หมายเหตุ', {
            'fields': ('notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def loan_amount_display(self, obj):
        return f'{obj.loan_amount:,.0f} บาท'
    loan_amount_display.short_description = 'จำนวนเงินกู้'

    def status_display(self, obj):
        status_colors = {
            'draft': '#9e9e9e',
            'submitted': '#2196f3',
            'under_review': '#ff9800',
            'approved': '#4caf50',
            'rejected': '#f44336',
            'cancelled': '#9e9e9e'
        }
        color = status_colors.get(obj.status, '#9e9e9e')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'สถานะ'

    def banks_count(self, obj):
        count = obj.application_banks.count()
        if count > 0:
            url = reverse('admin:refinance_applicationbank_changelist')
            return format_html(
                '<a href="{}?application__id__exact={}">{} ธนาคาร</a>',
                url, obj.pk, count
            )
        return "0 ธนาคาร"
    banks_count.short_description = 'ธนาคารที่สมัคร'


@admin.register(ApplicationBank)
class ApplicationBankAdmin(admin.ModelAdmin):
    list_display = [
        'application', 'bank', 'loan_product', 'status_display',
        'offered_rate_display', 'offered_amount_display', 'submitted_at'
    ]
    list_filter = ['status', 'bank', 'submitted_at']
    search_fields = ['application__application_no', 'bank__name']
    ordering = ['-submitted_at']

    def status_display(self, obj):
        status_colors = {
            'submitted': '#2196f3',
            'under_review': '#ff9800',
            'approved': '#4caf50',
            'rejected': '#f44336'
        }
        color = status_colors.get(obj.status, '#9e9e9e')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'สถานะ'

    def offered_rate_display(self, obj):
        if obj.offered_rate:
            return f'{obj.offered_rate:.2f}%'
        return '-'
    offered_rate_display.short_description = 'อัตราที่เสนอ'

    def offered_amount_display(self, obj):
        if obj.offered_amount:
            return f'{obj.offered_amount:,.0f} บาท'
        return '-'
    offered_amount_display.short_description = 'วงเงินที่อนุมัติ'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'document_type', 'application', 'file_size',
        'verification_status', 'uploaded_at'
    ]
    list_filter = [
        'document_type', 'is_verified', 'uploaded_at'
    ]
    search_fields = ['name', 'user__username', 'application__application_no']
    ordering = ['-uploaded_at']

    def file_size(self, obj):
        if obj.file:
            size = obj.file.size
            if size < 1024 * 1024:
                return f'{size / 1024:.1f} KB'
            else:
                return f'{size / (1024 * 1024):.1f} MB'
        return '-'
    file_size.short_description = 'ขนาดไฟล์'

    def verification_status(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="color: #4caf50;">● ตรวจสอบแล้ว</span><br>'
                '<small>โดย: {}</small>',
                obj.verified_by.username if obj.verified_by else 'ระบบ'
            )
        return format_html('<span style="color: #ff9800;">● รอตรวจสอบ</span>')
    verification_status.short_description = 'สถานะการตรวจสอบ'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'activity_type', 'description', 'ip_address', 'created_at'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'description', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'setting_type', 'category', 'is_public']
    list_filter = ['setting_type', 'category', 'is_public']
    search_fields = ['key', 'description']
    ordering = ['category', 'key']

    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('key', 'value', 'setting_type')
        }),
        ('รายละเอียด', {
            'fields': ('description', 'category', 'is_public')
        }),
    )

    def value_preview(self, obj):
        if len(obj.value) > 50:
            return f'{obj.value[:47]}...'
        return obj.value
    value_preview.short_description = 'ค่า'


@admin.register(InterestRateHistory)
class InterestRateHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'bank', 'loan_product', 'interest_rate_display', 'effective_date',
        'notes', 'created_at'
    ]
    list_filter = ['bank', 'effective_date', 'created_at']
    search_fields = ['bank__name', 'loan_product__name', 'notes']
    ordering = ['-effective_date', 'bank__name']

    def interest_rate_display(self, obj):
        return f'{obj.interest_rate:.2f}%'
    interest_rate_display.short_description = 'อัตราดอกเบี้ย'

    def has_change_permission(self, request, obj=None):
        return False

# Custom admin actions
def export_to_excel(modeladmin, request, queryset):
    pass

def bulk_activate(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        f'เปิดใช้งาน {updated} รายการเรียบร้อยแล้ว'
    )

def bulk_deactivate(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        f'ปิดใช้งาน {updated} รายการเรียบร้อยแล้ว'
    )

BankAdmin.actions = [bulk_activate, bulk_deactivate, export_to_excel]
LoanProductAdmin.actions = [bulk_activate, bulk_deactivate, export_to_excel]
PromotionAdmin.actions = [bulk_activate, bulk_deactivate, export_to_excel]