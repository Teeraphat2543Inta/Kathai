# refinance/views.py
from decimal import Decimal, InvalidOperation
from .models import ApplicationBank
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import logging
from django.urls import reverse  # <-- เพิ่มบรรทัดนี้เข้ามา
from .models import Advertisement
from formtools.wizard.views import SessionWizardView
from .models import Property, ActivityLog, Province, Bank, LoanProduct, LoanApplication, Document # เพิ่ม Province และ Models อื่นๆ ที่คุณใช้ใน Views
from .forms import PropertyForm

logger = logging.getLogger(__name__)

# **สำคัญ:** ต้อง import models ที่เกี่ยวข้องด้วย
from .models import Property, ActivityLog # สมมติว่ามี Property และ ActivityLog model
from .forms import PropertyForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal
from django.utils import timezone

# ---- Helpers to read bank contact fields safely ----
def _get_bank_phone(bank):
    candidates = [
        'phone_number', 'phone', 'contact_phone',
        'hotline', 'support_phone', 'tel', 'telephone', 'mobile'
    ]
    for field in candidates:
        val = getattr(bank, field, None)
        if val:
            return str(val).strip()
    # ลองดูใน field รวมๆ (เผื่อเก็บเป็น JSON/text)
    for field in ['contact_info', 'contacts', 'meta']:
        val = getattr(bank, field, None)
        if isinstance(val, dict):
            for k in ['phone', 'phone_number', 'hotline', 'tel']:
                if val.get(k):
                    return str(val[k]).strip()
        elif isinstance(val, str) and val:
            # ไม่ parse JSON เพื่อให้ปลอดภัย, แต่อย่างน้อยรีเทิร์นข้อความ
            return val.strip()
    return ''

def _get_bank_email(bank):
    candidates = [
        'email', 'contact_email', 'support_email', 'cs_email'
    ]
    for field in candidates:
        val = getattr(bank, field, None)
        if val:
            return str(val).strip()
    for field in ['contact_info', 'contacts', 'meta']:
        val = getattr(bank, field, None)
        if isinstance(val, dict):
            for k in ['email', 'contact_email', 'support_email']:
                if val.get(k):
                    return str(val[k]).strip()
        elif isinstance(val, str) and ('@' in val):
            return val.strip()
    return ''


@login_required
def advertisement_list_view(request):
    """
    แสดงรายการโปรโมชั่นและข่าวสารทั้งหมด
    """
    # ดึงโปรโมชั่นทั้งหมด เรียงตามวันที่สร้างล่าสุด
    # สมมติว่ามี field 'created_at' ใน Advertisement model
    advertisements = Advertisement.objects.all().order_by('-created_at')

    context = {
        'advertisements': advertisements
    }
    return render(request, 'refinance/advertisement_list.html', context)

@login_required
def get_loan_products_by_property_api(request, property_id):
    # คุณอาจจะต้องมี logic ในการกรอง LoanProduct ที่เกี่ยวข้องกับ Property นั้น
    # เช่น LoanProduct ที่รองรับประเภททรัพย์สินนั้นๆ หรือธนาคารที่อยู่ในพื้นที่นั้นๆ
    # สำหรับตัวอย่างนี้ จะดึง LoanProduct ทั้งหมด หรือคุณอาจจะกรองตาม Bank ที่เกี่ยวข้อง

    # ตัวอย่าง: ดึง LoanProduct ทั้งหมด หรือตามเงื่อนไขที่เหมาะสม
    # หากคุณต้องการกรองตาม property_id จริงๆ อาจจะต้องมีความสัมพันธ์ใน LoanProduct Model
    # ที่เชื่อมโยงกับ Property หรือ Bank ที่เกี่ยวข้องกับ Property นั้นๆ

    # ตัวอย่างเบื้องต้น: ดึง LoanProduct ทั้งหมด
    loan_products = LoanProduct.objects.all() 

    # หากคุณต้องการกรองตาม property type หรือ location ของ property
    # property = get_object_or_404(Property, pk=property_id, user=request.user)
    # loan_products = LoanProduct.objects.filter(supported_property_types=property.property_type) # ตัวอย่างการกรอง
    data = []
    for product in loan_products:
        data.append({
            'id': product.id,
            'bank_name': product.bank.name if product.bank else 'N/A', # ต้องมี field bank ใน LoanProduct
            'product_name': product.name,
            'min_interest_rate': str(product.min_interest_rate) if product.min_interest_rate else None,
            'max_interest_rate': str(product.max_interest_rate) if product.max_interest_rate else None,
            'description': product.description,
            'suggested_loan_amount': str(product.suggested_loan_amount) if hasattr(product, 'suggested_loan_amount') else None, # ถ้ามี field นี้ใน model
            'suggested_loan_term': str(product.suggested_loan_term) if hasattr(product, 'suggested_loan_term') else None, # ถ้ามี field นี้ใน model
            # เพิ่มฟิลด์อื่นๆ ที่คุณต้องการส่งไปยัง frontend
        })
    return JsonResponse(data, safe=False) # safe=False ถ้า list of dicts


@login_required
def get_property_details_api(request, property_id):
    """
    API endpoint เพื่อดึงข้อมูลทรัพย์สินเดี่ยวในรูปแบบ JSON
    """
    try:
        property_obj = get_object_or_404(Property, pk=property_id, user=request.user) # กรองตาม user ด้วยเพื่อความปลอดภัย

        data = {
            'id': property_obj.id,
            'name': property_obj.name, # เพิ่ม name ของทรัพย์สินด้วย
            'property_type': property_obj.property_type,
            'address': property_obj.address,
            'province': property_obj.province.id, # ส่ง ID ของจังหวัด
            'postal_code': property_obj.postal_code,
            'estimated_value': str(property_obj.estimated_value),
            'purchase_price': str(property_obj.purchase_price) if property_obj.purchase_price is not None else '',
            'purchase_date': property_obj.purchase_date.isoformat() if property_obj.purchase_date else '', # แปลงเป็น ISO format สำหรับวันที่
            'land_size': str(property_obj.land_size) if property_obj.land_size is not None else '', # แก้ไขเป็น land_size
            'building_size': str(property_obj.building_size) if property_obj.building_size is not None else '', # แก้ไขเป็น building_size
            'has_existing_loan': property_obj.has_existing_loan,
            'existing_loan_balance': str(property_obj.existing_loan_balance) if property_obj.existing_loan_balance is not None else '',
            'existing_bank': property_obj.existing_bank.id if property_obj.existing_bank else '', # ส่ง ID ของธนาคาร
        }
        return JsonResponse(data)
    except Property.DoesNotExist:
        return JsonResponse({'error': 'Property not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_property_details_api: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

# ต้อง import models ที่เกี่ยวข้อง
def loan_comparison_results_view(request):
    """
    Renders the loan comparison results page.
    You might want to add logic here later to fetch and pass comparison data.
    """
    # For now, we'll just render the template.
    # In a real application, you would typically fetch and process data here
    # to populate the loan_comparison_results.html template.
    context = {
        # 'results_data': some_data_from_database,
        # 'input_data': some_user_input_summary,
    }
    return render(request, 'refinance/loan_comparison_results.html', context)

from urllib.parse import urlencode # ต้อง import อันนี้ด้วย
# ตรวจสอบให้แน่ใจว่าได้ import models ที่เกี่ยวข้องแล้ว
# เช่น:
# from .models import LoanProduct, Bank, Property # ถ้ามี model เหล่านี้

# ... (View functions อื่นๆ ที่มีอยู่แล้ว) ...

def apply_loan(request, product_id):
    """
    จัดการการกดปุ่ม 'สมัครเลย' จากหน้าสรุปการเปรียบเทียบ
    จะเปลี่ยนเส้นทางไปยังหน้าสร้างคำขอสินเชื่อพร้อมข้อมูลที่กรอกไว้
    """
    try:
        # ดึงข้อมูล LoanProduct ที่ถูกเลือก
        # ตรวจสอบให้แน่ใจว่าได้ import LoanProduct model แล้ว
        loan_product = get_object_or_404(LoanProduct, pk=product_id)
    except NameError:
        messages.error(request, "Error: 'LoanProduct' model not found. Please ensure it's imported in views.py (e.g., from .models import LoanProduct).")
        return redirect('refinance:loan_summary_comparison')
    except Exception as e:
        messages.error(request, f"Error fetching loan product: {e}")
        return redirect('refinance:loan_summary_comparison')

    # รวบรวมข้อมูลเริ่มต้นที่จะใช้ Pre-fill ฟอร์ม
    initial_data = {
        'product_id': product_id, # ID ของผลิตภัณฑ์สินเชื่อที่เลือก
    }

    # ดึง bank_id จาก LoanProduct ที่เลือก เพื่อ Pre-fill ใน selected_banks
    # ตรวจสอบว่า loan_product มี field 'bank' ที่เป็น ForeignKey ไปยัง Bank model
    if hasattr(loan_product, 'bank') and loan_product.bank:
        initial_data['bank_id'] = loan_product.bank.id # ID ของธนาคาร

    # ดึงข้อมูลที่เคยกรอกใน Loan Comparison Wizard (ถ้าเก็บไว้ใน session)
    # **สำคัญ:** ชื่อคีย์ใน request.session ('loan_amount', 'loan_term', 'purpose', 'property_id')
    # ต้องตรงกับที่คุณบันทึกไว้จริงใน session จาก LoanComparisonWizard ของคุณ
    # หากไม่ได้เก็บใน session หรือมีชื่อคีย์ต่างกัน คุณต้องปรับเปลี่ยนส่วนนี้
    if 'loan_amount' in request.session:
        initial_data['loan_amount'] = request.session['loan_amount']
    if 'loan_term' in request.session:
        initial_data['loan_term'] = request.session['loan_term']
    if 'purpose' in request.session:
        initial_data['purpose'] = request.session['purpose']
    if 'property_id' in request.session: # ID ของทรัพย์สินที่เลือก
        initial_data['property_id'] = request.session['property_id']

    # สร้าง URL สำหรับเปลี่ยนเส้นทาง พร้อมแนบข้อมูลในรูปแบบ query parameters
    redirect_url = reverse('refinance:application_create')

    # กรองค่า None ออกก่อนแปลงเป็น query string
    query_string = urlencode({k: v for k, v in initial_data.items() if v is not None})
    if query_string:
        redirect_url += '?' + query_string

    return redirect(redirect_url)


def loan_summary_comparison_view(request):
    """
    หน้าสรุปการเปรียบเทียบ (Summary) — คำนวณจริงจากฐานข้อมูล
    และคำนวณเงินที่ประหยัดได้ (ประมาณ) แบบมี fallback เสมอ
    """
    if request.method != 'POST':
        messages.error(request, "กรุณาเลือกสินเชื่อที่ต้องการเปรียบเทียบจากหน้าผลลัพธ์")
        return redirect('refinance:loan_comparison_results')

    selected_product_ids = request.POST.getlist('selected_products')

    if not selected_product_ids:
        messages.error(request, "กรุณาเลือกสินเชื่อที่ต้องการเปรียบเทียบอย่างน้อย 2 รายการ")
        return redirect('refinance:loan_comparison_results')
    if len(selected_product_ids) < 2 or len(selected_product_ids) > 5:
        messages.error(request, "คุณสามารถเลือกสินเชื่อเพื่อเปรียบเทียบได้ 2 ถึง 5 รายการเท่านั้น")
        return redirect('refinance:loan_comparison_results')

    # ดึงข้อมูลสินเชื่อจริงจากฐานข้อมูล
    products_qs = (
        LoanProduct.objects
        .filter(id__in=selected_product_ids, is_active=True)
        .select_related('bank')
        .prefetch_related('bank__promotions', 'bank__fees', 'bank__fees__fee_type')
    )
    if not products_qs.exists():
        messages.error(request, "ไม่พบข้อมูลสินเชื่อที่เลือก กรุณาลองใหม่อีกครั้ง")
        return redirect('refinance:loan_comparison_results')

    # ข้อมูลจาก Wizard (ถ้ามี)
    wizard = request.session.get('wizard_loan_data', {}) or {}
    # พยายามดึง input พื้นฐาน
    try:
        loan_balance = Decimal(str(wizard.get('current_loan_balance') or '0'))
    except Exception:
        loan_balance = Decimal('0')
    # เผื่อไม่มีจาก wizard: ใช้ยอดกู้ขั้นต่ำของ product แรกเป็นสำรอง (จะไม่แม่น แต่ป้องกัน error)
    if loan_balance <= 0:
        # ลองเดาจาก min_loan_amount สูงสุดที่ยังมีค่า
        try:
            fallback_amounts = [Decimal(str(p.min_loan_amount)) for p in products_qs if p.min_loan_amount]
            if fallback_amounts:
                loan_balance = max(fallback_amounts)
        except Exception:
            pass
    if loan_balance <= 0:
        messages.error(request, "ไม่มีจำนวนเงินกู้สำหรับคำนวณ กรุณากรอกข้อมูลผ่าน Wizard อีกครั้ง")
        return redirect('refinance:loan_comparison_wizard')

    # อายุสัญญา (ปี) — ถ้าไม่มี ใช้ min ของชุดผลิตภัณฑ์เพื่อให้คำนวณได้จริง
    remaining_years = wizard.get('remaining_years', None)
    try:
        if isinstance(remaining_years, str):
            remaining_years = 35 if remaining_years == '30+' else int(remaining_years)
        remaining_years = int(remaining_years)
    except Exception:
        # ใช้ min ของ max_term_years ในชุดผลิตภัณฑ์เป็นสำรอง
        try:
            remaining_years = min([int(p.max_term_years or 20) for p in products_qs]) or 20
        except Exception:
            remaining_years = 20

    loan_term_months_default = remaining_years * 12

    def q2(n, places='0.01'):
        return Decimal(str(n)).quantize(Decimal(places), rounding=ROUND_HALF_UP)

    def calculate_monthly_payment(principal, annual_rate, months):
        """สูตร PMT แบบมาตรฐาน"""
        principal = Decimal(str(principal))
        annual_rate = Decimal(str(annual_rate))
        months = int(months)
        if months <= 0:
            return Decimal('0.00')
        r = annual_rate / Decimal('100') / Decimal('12')
        if r > 0:
            pmt = principal * (r * (1 + r) ** months) / ((1 + r) ** months - 1)
        else:
            pmt = principal / months
        return q2(pmt)

    rows = []
    best_product_id = None
    best_monthly = None

    # รอบที่ 1: คำนวณตัวเลขหลัก ๆ และเก็บ monthly_payment เพื่อหาฐานเปรียบเทียบ
    for product in products_qs:
        try:
            loan_term_years = min(remaining_years, int(product.max_term_years or remaining_years))
            loan_term_months = loan_term_years * 12

            # โปรโมชั่นดอกเบี้ย (ถ้ามี)
            promo = product.bank.promotions.filter(
                is_active=True,
                start_date__lte=timezone.now().date(),
                end_date__gte=timezone.now().date()
            ).filter(
                Q(min_loan_amount__isnull=True) | Q(min_loan_amount__lte=loan_balance),
                Q(max_loan_amount__isnull=True) | Q(max_loan_amount__gte=loan_balance)
            ).order_by('-priority').first()

            if promo and getattr(promo, 'special_rate', None):
                special_period = int(getattr(promo, 'special_rate_period', 12) or 12)
                first_year_rate = Decimal(str(promo.special_rate))
                second_year_rate = Decimal(str(promo.special_rate)) if special_period > 12 else Decimal(str(product.interest_rate))
                regular_rate = Decimal(str(product.interest_rate))
            else:
                first_year_rate = Decimal(str(product.interest_rate))
                second_year_rate = Decimal(str(product.interest_rate))
                regular_rate = Decimal(str(product.interest_rate))

            monthly_payment = calculate_monthly_payment(loan_balance, regular_rate, loan_term_months)
            total_payment = monthly_payment * loan_term_months
            total_interest = total_payment - loan_balance

            # ค่าธรรมเนียม
            try:
                processing_fee_amount = q2(loan_balance * Decimal(str(product.processing_fee or 0)) / 100)
            except Exception:
                processing_fee_amount = Decimal('0.00')
            try:
                appraisal_fee_amount = q2(product.appraisal_fee or 0)
            except Exception:
                appraisal_fee_amount = Decimal('0.00')

            legal_fee_amount = Decimal('0.00')
            other_fees = Decimal('0.00')
            try:
                for fee in product.bank.fees.filter(is_active=True):
                    code = getattr(fee.fee_type, 'code', '')
                    if code == 'legal_fee':
                        if fee.fee_type.fee_type == 'percentage':
                            legal_fee_amount = q2(loan_balance * Decimal(str(fee.amount)) / 100)
                        else:
                            legal_fee_amount = q2(fee.amount)
                    elif code not in ['processing_fee', 'appraisal_fee']:
                        if fee.fee_type.fee_type == 'percentage':
                            other_fees += q2(loan_balance * Decimal(str(fee.amount)) / 100)
                        else:
                            other_fees += q2(fee.amount)
            except Exception:
                # กันพลาด
                pass

            total_fees = processing_fee_amount + appraisal_fee_amount + legal_fee_amount + other_fees

            avg_3_year_rate = q2((first_year_rate + second_year_rate + regular_rate) / 3, '0.01')

            row = {
                'product_id': product.id,
                'bank_name': product.bank.name if product.bank else '',
                'product_name': product.name,
                'monthly_payment': monthly_payment,
                'avg_3_year_rate': avg_3_year_rate,
                'total_fees': total_fees,
                'total_interest': q2(total_interest, '0.01'),
                'loan_term_months': loan_term_months,  # เก็บไว้ใช้คำนวณ saving
                'promotion_title': getattr(promo, 'title', '') or 'ไม่มี',
            }
            rows.append(row)

            # หา best (ค่างวดต่ำสุด)
            if best_monthly is None or monthly_payment < best_monthly:
                best_monthly = monthly_payment
                best_product_id = product.id

        except Exception as e:
            print(f"[Summary] Error calculating product {getattr(product,'id','?')}: {e}")
            continue

    if not rows:
        messages.error(request, "ไม่สามารถคำนวณข้อมูลที่เลือกได้")
        return redirect('refinance:loan_comparison_results')

    # หา baseline สำหรับคำนวณ "เงินที่ประหยัดได้"
    # 1) จาก wizard (ถ้ามี)
    try:
        baseline_str = str(wizard.get('current_monthly_payment') or '0')
        baseline_monthly = Decimal(baseline_str)
    except Exception:
        baseline_monthly = Decimal('0')

    # 2) ถ้าไม่มี ให้ใช้ "ค่างวดสูงสุดในชุดที่เลือก" เป็น baseline
    if baseline_monthly <= 0:
        baseline_monthly = max([r['monthly_payment'] for r in rows])

    # รอบที่ 2: เติม savings_amount (รวมตลอดสัญญา) ให้ทุกแถว
    for r in rows:
        monthly_saving = baseline_monthly - r['monthly_payment']
        if monthly_saving < 0:
            monthly_saving = Decimal('0.00')
        savings_total = q2(monthly_saving * r['loan_term_months'], '0.01')
        r['savings_amount'] = savings_total
        # ไม่ส่ง loan_term_months ให้ template
        r.pop('loan_term_months', None)

    # เรียงตามค่างวด
    rows.sort(key=lambda x: x['monthly_payment'])

    context = {
        'summary_data': rows,
        'best_product_id': best_product_id,
        'input_data': wizard,  # เผื่อใช้โชว์สรุปอินพุต
    }
    return render(request, 'refinance/loan_summary_comparison.html', context)

# --- Import โมเดลทั้งหมดที่เกี่ยวข้อง ---
from refinance.models import (
    Province, Bank, LoanProduct, Promotion, FeeType, Fee, Property,
    LoanApplication, ApplicationBank, Document, ActivityLog,
    SystemSetting, InterestRateHistory
)

# --- Import ฟอร์มทั้งหมดที่เกี่ยวข้อง ---
from refinance.forms import (
    PropertyForm, LoanApplicationForm, DocumentUploadForm,
    RefinanceComparisonForm,
    LoanComparisonStep1Form,
    LoanComparisonStep2Form,
    UserRegistrationForm, ContactForm, BankFilterForm,
    PromotionFilterForm, QuickComparisonForm, NewsletterSubscriptionForm, FeedbackForm,
    PROPERTY_TYPE_CHOICES
)

# Set up logging
logger = logging.getLogger(__name__)

# กำหนดฟอร์มสำหรับแต่ละขั้นตอนของ Wizard
FORMS = [
    ("step1", LoanComparisonStep1Form),
    ("step2", LoanComparisonStep2Form),
]

# กำหนด template สำหรับแต่ละขั้นตอน
TEMPLATES = {
    "step1": "refinance/comparison_wizard_step1.html",
    "step2": "refinance/comparison_wizard_step2.html",
}

from .models import Bank # ตรวจสอบให้แน่ใจว่า import 'Bank' ถูกต้อง
# ถ้าคุณมี Promotion model ด้วย และอยากใช้ในหน้า home ก็ต้อง import ด้วย
# from .models import Promotion 

# ฟังก์ชันช่วยแบ่ง list ออกเป็นกลุ่มๆ
from .models import Bank # ตรวจสอบให้แน่ใจว่า import 'Bank' ถูกต้อง
# from .models import Promotion # ถ้าคุณมี Promotion model ด้วย ก็ต้อง import ด้วย

# ฟังก์ชันช่วยแบ่ง list ออกเป็นกลุ่มๆ
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def home(request):
    try:
        featured_banks = Bank.objects.filter(is_active=True, is_featured=True).order_by('name')
        featured_banks_chunks = list(chunks(featured_banks, 6))

        advertisements = Advertisement.objects.filter(is_active=True).order_by('-created_at')

        context = {
            'featured_banks': featured_banks,
            'featured_banks_chunks': featured_banks_chunks,
            'advertisements': advertisements,
        }
        # *** แก้ไขตรงนี้: เปลี่ยน 'index.html' เป็น 'home.html' ***
        return render(request, 'home.html', context)

    except Exception as e:
        print(f"Error in home view: {e}")
        # *** แก้ไขตรงนี้: เปลี่ยน 'index.html' เป็น 'home.html' ***
        return render(request, 'home.html', {
            'featured_banks': [],
            'featured_banks_chunks': [],
            'advertisements': []
        })
class LoanComparisonWizard(SessionWizardView):
    """
    Loan Comparison Wizard with real database integration (no mock)
    - Persist wizard inputs into session
    - Compute comparison using REAL DB data
    - Compute savings vs. user's current monthly payment (if provided)
    """

    def get_template_names(self):
        current_step = self.steps.current
        if current_step in TEMPLATES:
            return [TEMPLATES[current_step]]
        return ['refinance/comparison_wizard_step1.html']

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        current_step_index = self.steps.step0
        total_steps = self.steps.count
        display_percent = int(((current_step_index + 1) / total_steps) * 100) if total_steps > 0 else 0
        context['display_percent'] = display_percent

        if self.steps.current == 'step1':
            context['current_loan_balance_display'] = getattr(form, 'cleaned_data', {}).get('current_loan_balance', 0)
        return context

    def post(self, request, *args, **kwargs):
        current_step = self.steps.current

        if request.method == 'POST':
            form = self.get_form(current_step, request.POST, request.FILES)
            if form.is_valid():
                self.storage.set_step_data(current_step, self.process_step(form))
                self.storage.set_step_files(current_step, self.process_step_files(form))

        return super().post(request, *args, **kwargs)

    def get_form(self, step=None, data=None, files=None):
        if step is None:
            step = self.steps.current

        if data is None:
            step_data = self.storage.get_step_data(step)
            if step_data:
                form = super().get_form(step, step_data, files)
            else:
                form = super().get_form(step, data, files)
        else:
            form = super().get_form(step, data, files)

        # optional debug:
        # if (data is not None or self.storage.get_step_data(step)) and not form.is_valid():
        #     print(f"Form errors: {form.errors}")
        return form

    def process_step(self, form):
        return super().process_step(form)

    def render_done(self, form, **kwargs):
        # ตรวจสอบว่ามีข้อมูลครบทั้งสองสเต็ป
        step1_data = self.storage.get_step_data('step1')
        step2_data = self.storage.get_step_data('step2')

        if not step1_data or not step2_data:
            messages.error(self.request, "ข้อมูลไม่ครบถ้วน กรุณากรอกข้อมูลใหม่")
            self.storage.current_step = 'step1'
            return redirect('refinance:loan_comparison_wizard')

        try:
            step1_form = self.get_form('step1', step1_data)
            step2_form = self.get_form('step2', step2_data)
            return self.done([step1_form, step2_form], **kwargs)
        except Exception:
            messages.error(self.request, "เกิดข้อผิดพลาดในการประมวลผล")
            return redirect('refinance:loan_comparison_wizard')

    def done(self, form_list, **kwargs):
        """
        Enhanced done method with REAL database data + persist wizard inputs into session
        """
        all_data = {}

        for i, form in enumerate(form_list):
            if form.is_valid():
                all_data.update(form.cleaned_data)
            else:
                messages.error(self.request, f"ข้อผิดพลาดในแบบฟอร์มขั้นตอนที่ {i+1}")
                return redirect('refinance:loan_comparison_wizard')

        # ตรวจฟิลด์จำเป็น
        required_fields = ['property_price', 'current_loan_balance', 'monthly_income']
        missing = [f for f in required_fields if f not in all_data or not all_data[f]]
        if missing:
            messages.error(self.request, f"ข้อมูลไม่ครบถ้วน: {', '.join(missing)}")
            return redirect('refinance:loan_comparison_wizard')

        # แปลงเป็น Decimal/Int อย่างปลอดภัย
        try:
            property_price = Decimal(str(all_data['property_price']))
            loan_balance   = Decimal(str(all_data['current_loan_balance']))
            income         = Decimal(str(all_data['monthly_income']))
        except (InvalidOperation, ValueError):
            messages.error(self.request, "รูปแบบตัวเลขไม่ถูกต้อง")
            return redirect('refinance:loan_comparison_wizard')

        remaining_years = all_data.get('remaining_years', 20)
        try:
            remaining_years_int = 35 if str(remaining_years) == '30+' else int(remaining_years)
        except Exception:
            remaining_years_int = 20

        # --- เก็บลง session เพื่อใช้ต่อ (results/summary/apply_loan) ---
        try:
            session_payload = {
                'property_price': str(property_price),
                'current_loan_balance': str(loan_balance),
                'monthly_income': str(income),
                'remaining_years': remaining_years_int,
                'current_monthly_payment': str(all_data.get('current_monthly_payment') or 0),
                'property_type': str(all_data.get('property_type', '')),
                'province': str(all_data.get('province', '')),
                'occupation': str(all_data.get('occupation', '')),
                'current_bank': str(all_data.get('current_bank', '')),
                'need_extra_loan': str(all_data.get('need_extra_loan', '')),
            }
            for k in ('loan_amount', 'loan_term', 'purpose', 'property_id'):
                if k in all_data and all_data[k] not in (None, ''):
                    session_payload[k] = str(all_data[k])

            self.request.session['wizard_loan_data'] = session_payload
            for k in ('loan_amount', 'loan_term', 'purpose', 'property_id'):
                if k in session_payload:
                    self.request.session[k] = session_payload[k]
            self.request.session.modified = True
        except Exception as e:
            logger.warning(f"Cannot persist wizard_loan_data: {e}")

        # baseline (ค่างวดเดิม) - จากฟอร์มหรือจาก session
        baseline_payment = None
        try:
            if all_data.get('current_monthly_payment'):
                baseline_payment = Decimal(str(all_data['current_monthly_payment']))
        except (InvalidOperation, ValueError):
            baseline_payment = None

        if baseline_payment is None:
            sess = self.request.session.get('wizard_loan_data', {})
            if sess and sess.get('current_monthly_payment'):
                try:
                    baseline_payment = Decimal(str(sess['current_monthly_payment']))
                except (InvalidOperation, ValueError):
                    baseline_payment = None

        # LTV
        ltv = (loan_balance / property_price * 100) if property_price > 0 else Decimal('0')

        # Query ผลิตภัณฑ์จากฐานข้อมูลจริง
        eligible_products = LoanProduct.objects.filter(
            is_active=True,
            product_type='refinance',
            min_loan_amount__lte=loan_balance,
            max_loan_amount__gte=loan_balance,
            max_ltv__gte=ltv,
            min_income__lte=income,
            max_term_years__gte=remaining_years_int
        ).select_related('bank').prefetch_related(
            'bank__promotions',
            'bank__fees',
            'bank__fees__fee_type'
        ).order_by('interest_rate')

        def calculate_monthly_payment(principal, annual_rate, months):
            if months <= 0:
                return Decimal('0')
            monthly_rate = annual_rate / 100 / 12
            if monthly_rate > 0:
                p = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
            else:
                p = principal / months
            return Decimal(str(p)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        comparison_data = []

        for product in eligible_products:
            try:
                loan_term_years  = min(remaining_years_int, product.max_term_years)
                loan_term_months = loan_term_years * 12

                # โปรโมชั่น active ของธนาคาร (เงื่อนไขตามจริง)
                active_promo = product.bank.promotions.filter(
                    is_active=True,
                    start_date__lte=timezone.now().date(),
                    end_date__gte=timezone.now().date()
                ).filter(
                    Q(min_loan_amount__isnull=True) | Q(min_loan_amount__lte=loan_balance),
                    Q(max_loan_amount__isnull=True) | Q(max_loan_amount__gte=loan_balance)
                ).order_by('-priority').first()

                if active_promo and active_promo.special_rate:
                    special_period_months = active_promo.special_rate_period or 12
                    first_year_rate  = active_promo.special_rate
                    second_year_rate = active_promo.special_rate if special_period_months > 12 else product.interest_rate
                    regular_rate     = product.interest_rate
                else:
                    first_year_rate = second_year_rate = regular_rate = product.interest_rate

                monthly_payment     = calculate_monthly_payment(loan_balance, regular_rate,       loan_term_months)
                first_year_payment  = calculate_monthly_payment(loan_balance, first_year_rate,   loan_term_months)
                second_year_payment = calculate_monthly_payment(loan_balance, second_year_rate,  loan_term_months)

                avg_3_year_rate   = (first_year_rate + second_year_rate + regular_rate) / 3
                avg_lifetime_rate = regular_rate

                # ค่าธรรมเนียมจาก DB
                processing_fee_amount = (loan_balance * product.processing_fee / 100).quantize(Decimal('0.01')) if product.processing_fee else Decimal('0.00')
                appraisal_fee_amount  = product.appraisal_fee or Decimal('0.00')

                legal_fee_amount = Decimal('0.00')
                other_fees       = Decimal('0.00')
                try:
                    for fee in product.bank.fees.filter(is_active=True):
                        if fee.fee_type.code == 'legal_fee':
                            legal_fee_amount = ((loan_balance * fee.amount / 100).quantize(Decimal('0.01'))
                                                if fee.fee_type.fee_type == 'percentage' else fee.amount)
                        elif fee.fee_type.code not in ['processing_fee', 'appraisal_fee']:
                            other_fees += ((loan_balance * fee.amount / 100).quantize(Decimal('0.01'))
                                           if fee.fee_type.fee_type == 'percentage' else fee.amount)
                except Exception:
                    # fallback ปลอดภัย
                    pass

                total_fees     = processing_fee_amount + appraisal_fee_amount + legal_fee_amount + other_fees
                total_payment  = monthly_payment * loan_term_months
                total_interest = total_payment - loan_balance

                # savings เทียบ baseline (ถ้ามี)
                savings_amount = Decimal('0.00')
                if baseline_payment is not None and baseline_payment > monthly_payment:
                    savings_amount = ((baseline_payment - monthly_payment) * loan_term_months).quantize(Decimal('0.01'))

                promotion_title      = active_promo.title if active_promo else ""
                promotion_conditions = getattr(active_promo, 'terms_conditions', '') if active_promo else ""
                promotion_expiry     = active_promo.end_date if active_promo else None
                promotion_details    = active_promo.description if active_promo else "ไม่มีโปรโมชั่นพิเศษ"

                current_mrr      = Decimal('2.75')
                mrr_spread_value = regular_rate - current_mrr

                comparison_data.append({
                    'product': product,
                    'bank_name': product.bank.name,
                    'product_name': product.name,
                    'interest_rate': product.interest_rate,
                    'monthly_payment': monthly_payment,
                    'interest_rate_display': f'{product.interest_rate}%',
                    'promotion_details': promotion_details,
                    'processing_fee_amount': processing_fee_amount,
                    'appraisal_fee_amount': appraisal_fee_amount,
                    'total_payment': total_payment,
                    'total_interest': total_interest,

                    'first_year_rate': first_year_rate,
                    'second_year_rate': second_year_rate,
                    'regular_rate': regular_rate,
                    'first_year_payment': first_year_payment,
                    'second_year_payment': second_year_payment,
                    'regular_payment': monthly_payment,
                    'avg_3_year_rate': Decimal(str(avg_3_year_rate)).quantize(Decimal('0.01')),
                    'avg_lifetime_rate': avg_lifetime_rate,

                    'current_mrr': current_mrr,
                    'mrr_spread': f'+ {mrr_spread_value:.2f}%' if mrr_spread_value > 0 else f'{mrr_spread_value:.2f}%',
                    'max_term': product.max_term_years,
                    'interest_type_display': product.get_interest_rate_type_display(),
                    'is_step_payment': False,
                    'requires_life_insurance': True,
                    'requires_property_insurance': True,

                    'legal_fee_amount': legal_fee_amount,
                    'total_fees': total_fees,
                    'processing_fee_note': f'{product.processing_fee}% ของจำนวนเงินกู้' if product.processing_fee else 'ไม่มีค่าธรรมเนียม',
                    'appraisal_fee_note': 'ค่าประเมินทรัพย์สิน',
                    'legal_fee_note': 'ค่าธรรมเนียมกฎหมาย',

                    'promotion_title': promotion_title,
                    'promotion_conditions': promotion_conditions,
                    'promotion_expiry': promotion_expiry,

                    'savings_amount': savings_amount,
                })
            except Exception as e:
                # ข้าม product ที่คำนวณไม่ได้ เพื่อไม่ให้ทั้งหน้าล้ม
                continue

        # เรียงตามค่าผ่อนน้อยสุด และตัดเหลือ 5
        comparison_data.sort(key=lambda x: x['monthly_payment'])
        all_found_products_count = len(comparison_data)
        comparison_data = comparison_data[:5]

        dsr_ratio = (comparison_data[0]['monthly_payment'] / income * 100).quantize(Decimal('0.01')) if comparison_data and income > 0 else Decimal('0.00')

        context = {
            'comparison_data': comparison_data,
            'input_data': all_data,
            'results': comparison_data,
            'ltv_ratio': ltv,
            'dsr_ratio': dsr_ratio,
            'has_results': len(comparison_data) > 0,
            'total_products_found': all_found_products_count,
            'user_property_type': dict(PROPERTY_TYPE_CHOICES).get(all_data.get('property_type'), 'ไม่ระบุ'),
            'user_province': str(all_data.get('province', 'ไม่ระบุ')),
            'user_occupation': all_data.get('occupation', 'ไม่ระบุ'),
            'user_current_bank': str(all_data.get('current_bank', 'ไม่ระบุ')),
            'user_remaining_years': all_data.get('remaining_years', 'ไม่ระบุ'),
            'user_need_extra_loan': 'ต้องการ' if all_data.get('need_extra_loan') == 'yes' else 'ไม่ต้องการ',
        }
        return render(self.request, 'refinance/loan_comparison_results.html', context)

def refinance_comparison_form(request):
    """
    ฟังก์ชันสำหรับหน้าเปรียบเทียบแบบเดิม (สำรอง)
    ป้องกันข้อผิดพลาดทุกกรณี
    """
    try:
        if request.method == 'POST':
            form = RefinanceComparisonForm(request.POST)
            if form.is_valid():
                return _process_refinance_comparison(request, form)
        else:
            form = RefinanceComparisonForm()
        
        return render(request, 'refinance/refinance_comparison_form.html', {'form': form})
        
    except Exception as e:
        logger.error(f"Error in refinance_comparison_form: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่อีกครั้ง")
        return render(request, 'refinance/refinance_comparison_form.html', {'form': RefinanceComparisonForm()})


def _process_refinance_comparison(request, form):
    """ประมวลผลการเปรียบเทียบสินเชื่อ (สำหรับฟอร์มแบบเดิม)"""
    try:
        cleaned_data = form.cleaned_data
        property_price = cleaned_data['property_price']
        current_loan_balance = cleaned_data['current_loan_balance']
        monthly_income = cleaned_data['monthly_income']
        remaining_years = cleaned_data['remaining_years']

        # คำนวณ LTV
        calculated_ltv = Decimal('0.00')
        if property_price and property_price > 0:
            calculated_ltv = (current_loan_balance / property_price) * 100

        # ค้นหาผลิตภัณฑ์ที่เหมาะสม
        eligible_products = LoanProduct.objects.filter(
            is_active=True,
            product_type='refinance',
            min_loan_amount__lte=current_loan_balance,
            max_loan_amount__gte=current_loan_balance,
            max_ltv__gte=calculated_ltv,
            min_income__lte=monthly_income,
        ).select_related('bank').prefetch_related('promotions')

        # แปลง remaining_years เป็น int ถ้าเป็นไปได้
        try:
            remaining_years_int = int(remaining_years) if remaining_years != '30+' else 35
            eligible_products = eligible_products.filter(max_term_years__gte=remaining_years_int)
        except (ValueError, TypeError):
            pass  # ถ้าแปลงไม่ได้ก็ข้าม filter นี้

        comparison_data = []
        for product in eligible_products:
            try:
                estimated_new_term_months = product.max_term_years * 12
                if estimated_new_term_months <= 0:
                    continue

                # คำนวณค่าผ่อนรายเดือน
                principal = current_loan_balance
                monthly_rate = product.interest_rate / 100 / 12
                
                if monthly_rate > 0:
                    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** estimated_new_term_months) / ((1 + monthly_rate) ** estimated_new_term_months - 1)
                else:
                    monthly_payment = principal / estimated_new_term_months
                
                monthly_payment = monthly_payment.quantize(Decimal('0.01'))

                # คำนวณค่าธรรมเนียม
                processing_fee_amount = Decimal('0.00')
                if hasattr(product, 'processing_fee_type') and product.processing_fee_type == 'percentage':
                    if hasattr(product, 'processing_fee_value') and product.processing_fee_value is not None:
                        processing_fee_amount = (current_loan_balance * product.processing_fee_value / 100).quantize(Decimal('0.01'))
                elif hasattr(product, 'processing_fee_type') and product.processing_fee_type == 'fixed':
                    if hasattr(product, 'processing_fee_value') and product.processing_fee_value is not None:
                        processing_fee_amount = Decimal(str(product.processing_fee_value)).quantize(Decimal('0.01'))

                total_payment = monthly_payment * Decimal(estimated_new_term_months)

                # ดึงโปรโมชั่น
                active_promotions = []
                for promotion in product.promotions.all():
                    try:
                        if hasattr(promotion, 'is_valid_now') and promotion.is_valid_now():
                            active_promotions.append(promotion.title)
                        elif (promotion.is_active and 
                              promotion.start_date <= timezone.now().date() <= promotion.end_date):
                            active_promotions.append(promotion.title)
                    except:
                        continue

                promotion_details = ", ".join(active_promotions) if active_promotions else "ไม่มีโปรโมชั่นพิเศษ"

                comparison_data.append({
                    'product': product,
                    'monthly_payment': monthly_payment,
                    'processing_fee_amount': processing_fee_amount,
                    'total_payment': total_payment,
                    'promotion_details': promotion_details,
                })
            except Exception as e:
                logger.error(f"Error calculating for product {product.name} in refinance_comparison_form: {e}")
                continue

        comparison_data.sort(key=lambda x: x['monthly_payment'])

        context = {
            'form': form,
            'comparison_data': comparison_data,
            'input_data': cleaned_data,
            'ltv_ratio': calculated_ltv,
            'form_submitted': True,
            'results': comparison_data,
        }
        return render(request, 'refinance/loan_comparison_results.html', context)
        
    except Exception as e:
        logger.error(f"Error processing refinance comparison: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง")
        return render(request, 'refinance/refinance_comparison_form.html', {'form': form})

# --- Dashboard และ Property Views (ป้องกันข้อผิดพลาด) ---

@login_required
def dashboard_view(request):
    """แดชบอร์ดผู้ใช้ - ป้องกันข้อผิดพลาดทุกกรณี"""
    try:
        user_properties = Property.objects.filter(user=request.user).order_by('-created_at')[:5]
        user_applications = LoanApplication.objects.filter(user=request.user).order_by('-created_at')[:5]
        user_documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')[:5]
        activity_logs = ActivityLog.objects.filter(user=request.user).order_by('-created_at')[:10]

        context = {
            'user_properties': user_properties,
            'user_applications': user_applications,
            'user_documents': user_documents,
            'activity_logs': activity_logs,
        }
        return render(request, 'refinance/dashboard.html', context)
    except Exception as e:
        logger.error(f"Error in dashboard_view: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดแดชบอร์ด")
        return render(request, 'refinance/dashboard.html', {
            'user_properties': [],
            'user_applications': [],
            'user_documents': [],
            'activity_logs': [],
        })

@login_required
def property_list(request):
    """รายการทรัพย์สิน"""
    try:
        properties = Property.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'refinance/property_list.html', {'properties': properties})
    except Exception as e:
        logger.error(f"Error in property_list: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายการทรัพย์สิน")
        return render(request, 'refinance/property_list.html', {'properties': []})

@login_required
def property_detail(request, pk):
    """รายละเอียดทรัพย์สิน"""
    try:
        property_instance = get_object_or_404(Property, pk=pk, user=request.user)
        return render(request, 'refinance/property_detail.html', {'property': property_instance})
    except Property.DoesNotExist:
        messages.error(request, "ไม่พบทรัพย์สินที่ต้องการ")
        return redirect('refinance:property_list')
    except Exception as e:
        logger.error(f"Error in property_detail: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายละเอียดทรัพย์สิน")
        return redirect('refinance:property_list')

@login_required
@login_required
def property_create(request):
    """สร้างทรัพย์สินใหม่ หรือเลือกทรัพย์สินที่มีอยู่เพื่อแก้ไข/อ้างอิง"""
    try:
        if request.method == 'POST':
            form = PropertyForm(request.POST)
            if form.is_valid():
                property_instance = form.save(commit=False)
                property_instance.user = request.user # กำหนด user เจ้าของทรัพย์สิน
                property_instance.save()
                
                messages.success(request, 'ทรัพย์สินถูกบันทึกเรียบร้อยแล้ว!')
                
                # บันทึก Activity Log (ตรวจสอบว่า ActivityLog มี field 'description' และ 'user')
                try:
                    ActivityLog.objects.create(
                        user=request.user,
                        activity_type='property_add',
                        # สมมติว่า Property model มี field 'name' หรือ 'address'
                        # ให้เปลี่ยนตาม field ที่คุณใช้ระบุชื่อทรัพย์สิน
                        description=f'เพิ่มทรัพย์สิน: {property_instance.address}' 
                    )
                except Exception as log_error:
                    logger.error(f"Error creating activity log for property_add: {log_error}")
                
                return redirect('refinance:property_list')
            else:
                # ถ้าฟอร์มไม่ถูกต้องตอน POST ก็ยังคงต้องส่งรายการทรัพย์สินไปให้ template
                properties = Property.objects.filter(user=request.user) # กรองเฉพาะทรัพย์สินของ user ปัจจุบัน
                context = {
                    'form': form,
                    'properties': properties,
                }
                return render(request, 'refinance/property_form.html', context)
        else: # GET request หรือแสดงฟอร์มครั้งแรก
            form = PropertyForm()
            # ดึงทรัพย์สินทั้งหมดของ user ปัจจุบัน เพื่อใช้ใน dropdown
            properties = Property.objects.filter(user=request.user) 
            context = {
                'form': form,
                'properties': properties,
            }
            return render(request, 'refinance/property_form.html', context)
        
    except Exception as e:
        logger.error(f"Error in property_create: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการสร้างทรัพย์สิน")
        # ในกรณีเกิดข้อผิดพลาด ก็ยังคงต้องส่งฟอร์มเปล่าและรายการทรัพย์สินไป
        properties = Property.objects.filter(user=request.user)
        context = {
            'form': PropertyForm(),
            'properties': properties,
        }
        return render(request, 'refinance/property_form.html', context)
@login_required
def property_update(request, pk):
    """แก้ไขทรัพย์สิน"""
    try:
        property_instance = get_object_or_404(Property, pk=pk, user=request.user)
        
        if request.method == 'POST':
            form = PropertyForm(request.POST, instance=property_instance)
            if form.is_valid():
                form.save()
                messages.success(request, 'ข้อมูลทรัพย์สินถูกอัปเดตเรียบร้อยแล้ว!')
                
                # บันทึก Activity Log
                try:
                    ActivityLog.objects.create(
                        user=request.user,
                        activity_type='profile_update',
                        description=f'อัปเดตทรัพย์สิน: {property_instance.name}'
                    )
                except Exception as log_error:
                    logger.error(f"Error creating activity log: {log_error}")
                
                return redirect('refinance:property_detail', pk=pk)
        else:
            form = PropertyForm(instance=property_instance)
        
        return render(request, 'refinance/property_form.html', {'form': form})
        
    except Property.DoesNotExist:
        messages.error(request, "ไม่พบทรัพย์สินที่ต้องการแก้ไข")
        return redirect('refinance:property_list')
    except Exception as e:
        logger.error(f"Error in property_update: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการแก้ไขทรัพย์สิน")
        return redirect('refinance:property_list')

@login_required
def property_delete(request, pk):
    """ลบทรัพย์สิน"""
    try:
        property_instance = get_object_or_404(Property, pk=pk, user=request.user)
        
        if request.method == 'POST':
            property_name = property_instance.name
            property_instance.delete()
            messages.success(request, f'ทรัพย์สิน "{property_name}" ถูกลบเรียบร้อยแล้ว!')
            
            # บันทึก Activity Log
            try:
                ActivityLog.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=f'ลบทรัพย์สิน: {property_name}'
                )
            except Exception as log_error:
                logger.error(f"Error creating activity log: {log_error}")
            
            return redirect('refinance:property_list')
        
        return render(request, 'refinance/property_confirm_delete.html', {'property': property_instance})
        
    except Property.DoesNotExist:
        messages.error(request, "ไม่พบทรัพย์สินที่ต้องการลบ")
        return redirect('refinance:property_list')
    except Exception as e:
        logger.error(f"Error in property_delete: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการลบทรัพย์สิน")
        return redirect('refinance:property_list')

# --- Loan Application Views ---

@login_required
def loan_application_list(request):
    """รายการใบสมัครสินเชื่อ"""
    try:
        applications = LoanApplication.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'refinance/loan_application_list.html', {'applications': applications})
    except Exception as e:
        logger.error(f"Error in loan_application_list: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายการใบสมัคร")
        return render(request, 'refinance/loan_application_list.html', {'applications': []})

@login_required
def loan_application_detail(request, pk):
    """รายละเอียดใบสมัครสินเชื่อ"""
    try:
        application = get_object_or_404(LoanApplication, pk=pk, user=request.user)
        application_banks = application.application_banks.all()
        documents = application.documents.all()
        
        context = {
            'application': application,
            'application_banks': application_banks,
            'documents': documents
        }
        return render(request, 'refinance/loan_application_detail.html', context)
        
    except LoanApplication.DoesNotExist:
        messages.error(request, "ไม่พบใบสมัครที่ต้องการ")
        return redirect('refinance:loan_application_list')
    except Exception as e:
        logger.error(f"Error in loan_application_detail: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายละเอียดใบสมัคร")
        return redirect('refinance:loan_application_list')


from django import forms
from decimal import Decimal
from django.core.validators import RegexValidator

# ตรวจสอบให้แน่ใจว่าได้นำเข้าโมเดลที่จำเป็นทั้งหมดอย่างถูกต้อง
# เช่น Property, LoanApplication, Bank, ApplicationBank
from .models import Property, LoanApplication, Bank, ApplicationBank 

from django import forms
from django.forms import CheckboxSelectMultiple  # เพิ่ม import นี้
from .models import Property, LoanApplication, Bank

class LoanApplicationForm(forms.ModelForm):
    # ให้แสดงเป็น checkbox หลายตัว (เลือกได้หลายธนาคาร)
    selected_banks = forms.ModelMultipleChoiceField(
        queryset=Bank.objects.filter(is_active=True).order_by('name'),
        required=True,
        label='เลือกธนาคารที่ต้องการยื่นคำขอ',
        widget=CheckboxSelectMultiple(attrs={'class': 'bank-checkbox form-check-input'})  # สำคัญ
    )

    class Meta:
        model = LoanApplication
        # ไม่ต้องใส่ ManyToManyField ของ model (เช่น banks) ลงใน fields
        fields = [
            'property', 'loan_amount', 'loan_term', 'purpose',
            'monthly_income', 'monthly_expense', 'other_debts', 'notes'
        ]
        labels = {
            'property': 'เลือกทรัพย์สิน',
            'loan_amount': 'จำนวนเงินกู้ที่ต้องการ (บาท)',
            'loan_term': 'ระยะเวลากู้ (ปี)',
            'purpose': 'วัตถุประสงค์',
            'monthly_income': 'รายได้ต่อเดือน (บาท)',
            'monthly_expense': 'รายจ่ายต่อเดือน (บาท)',
            'other_debts': 'หนี้สินอื่น (บาท)',
            'notes': 'หมายเหตุ',
        }
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select', 'id': 'id_property'}),
            'loan_amount': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_loan_amount'}),
            'loan_term': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_loan_term'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_purpose'}),
            'monthly_income': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_monthly_income'}),
            'monthly_expense': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_monthly_expense'}),
            'other_debts': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_other_debts'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'id_notes'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # แสดงเฉพาะทรัพย์สินของผู้ใช้
        if user:
            self.fields['property'].queryset = Property.objects.filter(user=user)

        # ตั้งค่า default purpose
        if not self.initial.get('purpose'):
            self.initial['purpose'] = 'รีไฟแนนซ์สินเชื่อบ้าน'

        # ใส่ class ให้ checkbox แต่ละตัว (บางธีม Bootstrap ต้องการ)
        self.fields['selected_banks'].widget.attrs.update({'class': 'bank-checkbox'})

    def clean_selected_banks(self):
        qs = self.cleaned_data.get('selected_banks')
        if not qs or qs.count() == 0:
            raise forms.ValidationError('กรุณาเลือกธนาคารอย่างน้อย 1 แห่ง')
        return qs

        
        # หากฟอร์มมีการส่งข้อมูลกลับมา (เช่นเกิด validation error)
        # และมีค่า selected_banks อยู่ใน initial data (จาก form.errors.items())
        # เราจะใช้ค่าเหล่านั้นเพื่อ pre-select ธนาคารใน UI
        # ไม่ต้องทำอะไรเพิ่มเติมใน __init__ สำหรับการแสดงผล HTML/JS
        # Django จะจัดการ initial values ของ ModelMultipleChoiceField ให้เอง
        # ซึ่งจะถูกส่งไปที่ hidden select element ใน template

@login_required
def loan_application_create(request):
    """
    สร้างใบสมัครสินเชื่อใหม่
    - ปุ่ม 'ยื่นคำขอ'  => Application.status = submitted, ApplicationBank.status = submitted
    - ปุ่ม 'บันทึกร่าง' => Application.status = draft,     ApplicationBank.status = draft
    - บันทึก snapshot รายละเอียดผลิตภัณฑ์/การติดต่อจาก DB จริง
    """
    # 1) ผู้ใช้ต้องมีทรัพย์สินก่อน
    user_properties = Property.objects.filter(user=request.user)
    if not user_properties.exists():
        messages.warning(request, 'คุณต้องเพิ่มข้อมูลทรัพย์สินก่อนยื่นคำขอ')
        return redirect('refinance:property_add')

    # 2) initial จาก query string
    initial_data = {}
    pre_selected_loan_product_id = None
    preselected_bank_ids = []

    if request.method == 'GET':
        # รับค่า initial ทั่วไป
        for field in ['loan_amount', 'loan_term', 'purpose', 'property_id']:
            value = request.GET.get(field)
            if not value:
                continue
            if field == 'property_id':
                try:
                    prop = Property.objects.get(id=value, user=request.user)
                    initial_data['property'] = prop
                except Property.DoesNotExist:
                    pass
            else:
                initial_data[field] = value

        # ธนาคารที่เลือกจากหน้าก่อนหน้า (ถ้ามี)
        bank_id = request.GET.get('bank_id')
        if bank_id:
            try:
                bank = Bank.objects.get(id=bank_id, is_active=True)
                preselected_bank_ids = [str(bank.id)]
            except Bank.DoesNotExist:
                pass

        # loan_product ที่เลือกจากหน้าก่อนหน้า (ถ้ามี)
        pre_selected_loan_product_id = request.GET.get('loan_product_id')
        if pre_selected_loan_product_id:
            try:
                lp = LoanProduct.objects.get(pk=pre_selected_loan_product_id, is_active=True)
                if getattr(lp, 'suggested_loan_amount', None):
                    initial_data['loan_amount'] = lp.suggested_loan_amount
                if getattr(lp, 'suggested_loan_term', None):
                    initial_data['loan_term'] = lp.suggested_loan_term
            except LoanProduct.DoesNotExist:
                pass

    # 3) POST => validate & save
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, user=request.user)
        preselected_bank_ids = request.POST.getlist('selected_banks')  # ให้ติ๊กกลับในกรณี error

        if form.is_valid():
            try:
                with transaction.atomic():
                    # 3.1) Application
                    loan_application = form.save(commit=False)
                    loan_application.user = request.user

                    # Action จากปุ่ม
                    if 'save_draft' in request.POST:
                        action = 'draft'
                    elif 'submit_application' in request.POST or 'submit' in request.POST:
                        action = 'submit'
                    else:
                        action = 'submit'  # fallback

                    if action == 'submit':
                        loan_application.status = 'submitted'
                        loan_application.submitted_at = timezone.now()
                    else:
                        loan_application.status = 'draft'

                    loan_application.save()

                    # 3.2) ธนาคารที่เลือก (Many)
                    selected_banks = form.cleaned_data.get('selected_banks', [])

                    # กันโพสต์ซ้ำ ด้วยการลบความสัมพันธ์เก่า
                    ApplicationBank.objects.filter(application=loan_application).delete()

                    app_bank_status = 'submitted' if loan_application.status == 'submitted' else 'draft'
                    today = timezone.now().date()

                    for bank in selected_banks:
                        # เลือกผลิตภัณฑ์รีไฟแนนซ์ที่ดอกเบี้ยต่ำสุดของธนาคารนั้น (ถ้ามี)
                        product_obj = LoanProduct.objects.filter(
                            bank=bank, is_active=True, product_type='refinance'
                        ).order_by('interest_rate').first()

                        # โปรโมชั่นที่ active (ถ้ามี)
                        if hasattr(Promotion, 'priority'):
                            promotion_obj = Promotion.objects.filter(
                                bank=bank, is_active=True,
                                start_date__lte=today, end_date__gte=today
                            ).order_by('-priority').first()
                        else:
                            promotion_obj = Promotion.objects.filter(
                                bank=bank, is_active=True,
                                start_date__lte=today, end_date__gte=today
                            ).first()

                        # snapshot: ติดต่อธนาคาร
                        bank_phone = _get_bank_phone(bank)
                        bank_email = _get_bank_email(bank)

                        # snapshot: ฟิลด์ผลิตภัณฑ์
                        product_name_snapshot = product_obj.name if product_obj else ''
                        interest_rate_snapshot = getattr(product_obj, 'interest_rate', None) if product_obj else None
                        max_ltv_snapshot = getattr(product_obj, 'max_ltv', None) if product_obj else None
                        max_term_years_snapshot = getattr(product_obj, 'max_term_years', None) if product_obj else None
                        processing_fee_percent_snapshot = getattr(product_obj, 'processing_fee', None) if product_obj else None
                        product_note_snapshot = getattr(product_obj, 'description', '') if product_obj else ''

                        # 3.3) บันทึก ApplicationBank (ครั้งเดียว/ธนาคาร)
                        ApplicationBank.objects.create(
                            application=loan_application,
                            bank=bank,
                            loan_product=product_obj,
                            promotion=promotion_obj,
                            status=app_bank_status,
                            # snapshots
                            contact_phone_snapshot=bank_phone,
                            contact_email_snapshot=bank_email,
                            product_name_snapshot=product_name_snapshot,
                            interest_rate_snapshot=interest_rate_snapshot,
                            max_ltv_snapshot=max_ltv_snapshot,
                            max_term_years_snapshot=max_term_years_snapshot,
                            processing_fee_percent_snapshot=processing_fee_percent_snapshot,
                            product_note_snapshot=product_note_snapshot,
                        )

                    # (ออปชัน) นับจำนวนธนาคารที่ยื่น
                    if hasattr(loan_application, 'applied_bank_count'):
                        loan_application.applied_bank_count = len(selected_banks)
                        loan_application.save(update_fields=['applied_bank_count'])

                    # 3.4) Log กิจกรรม
                    try:
                        ActivityLog.objects.create(
                            user=request.user,
                            activity_type='loan_application',
                            description=f'บันทึกคำขอสินเชื่อ: {loan_application.application_no}',
                            details={'status': loan_application.status,
                                     'banks': [b.id for b in selected_banks]}
                        )
                    except Exception:
                        pass

                    # 3.5) แจ้งผลและไปหน้ารายละเอียด
                    if loan_application.status == 'submitted':
                        messages.success(
                            request,
                            f'ยื่นคำขอรีไฟแนนซ์สำเร็จแล้ว! หมายเลขคำขอ: {loan_application.application_no}'
                        )
                    else:
                        messages.success(request, 'บันทึกร่างคำขอเรียบร้อยแล้ว')

                    return redirect('refinance:loan_application_detail', pk=loan_application.pk)

            except Exception as e:
                messages.error(request, f'เกิดข้อผิดพลาดในการยื่นคำขอ: {str(e)}')

        else:
            # แสดง error รายฟิลด์
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_label}: {error}")
            for error in form.non_field_errors():
                messages.error(request, error)

    else:
        form = LoanApplicationForm(initial=initial_data, user=request.user)

    # 4) ธนาคาร + สถิติสำหรับ UI (ไม่ mock)
    today = timezone.now().date()
    all_banks = Bank.objects.filter(is_active=True).order_by('display_order', 'name') \
        .prefetch_related('promotions', 'fees__fee_type')

    banks_with_stats = []
    for bank in all_banks:
        products_qs = LoanProduct.objects.filter(
            bank=bank, is_active=True, product_type='refinance'
        ).only('interest_rate', 'max_ltv', 'max_term_years', 'min_income', 'processing_fee', 'name')

        product_count = products_qs.count()
        min_interest = products_qs.order_by('interest_rate').values_list('interest_rate', flat=True).first()
        max_ltv = products_qs.order_by('-max_ltv').values_list('max_ltv', flat=True).first()
        max_term = products_qs.order_by('-max_term_years').values_list('max_term_years', flat=True).first()
        min_income = products_qs.order_by('min_income').values_list('min_income', flat=True).first()
        best_product = products_qs.order_by('interest_rate').first()
        best_product_name = best_product.name if best_product else ''

        active_promos = list(
            bank.promotions.filter(
                is_active=True, start_date__lte=today, end_date__gte=today
            ).values_list('title', flat=True)[:2]
        )
        processing_fee_percent = products_qs.values_list('processing_fee', flat=True).first()

        banks_with_stats.append({
            'bank': bank,
            'product_count': product_count or 0,
            'min_interest': float(min_interest) if min_interest is not None else None,
            'max_ltv': float(max_ltv) if max_ltv is not None else None,
            'max_term': int(max_term) if max_term is not None else None,
            'min_income': float(min_income) if min_income is not None else None,
            'processing_fee_percent': float(processing_fee_percent) if processing_fee_percent is not None else None,
            'active_promos': active_promos,
            'best_product_name': best_product_name,
        })

    # 5) properties_json + recommended_products_json สำหรับ JS
    props_map = {}
    for p in user_properties.select_related('province', 'existing_bank'):
        try:
            ltv_val = 0.0
            if p.estimated_value and p.estimated_value > 0 and p.existing_loan_balance:
                ltv_val = float(p.existing_loan_balance / p.estimated_value * 100)
            props_map[str(p.id)] = {
                'type': getattr(p, 'property_type', '') or '',
                'value': float(p.estimated_value or 0),
                'province': str(getattr(p.province, 'name', '') or ''),
                'current_debt': float(p.existing_loan_balance or 0),
                'current_bank': str(getattr(p.existing_bank, 'name', '') or ''),
                'ltv': round(ltv_val, 2),
            }
        except Exception:
            continue

    properties_json = json.dumps(props_map, ensure_ascii=False)

    top_products = list(
        LoanProduct.objects.filter(
            is_active=True, product_type='refinance'
        ).select_related('bank').order_by('interest_rate').values(
            'id', 'name', 'bank__name', 'interest_rate'
        )[:4]
    )
    recommended_products = [{
        'id': tp['id'],
        'bank_name': tp['bank__name'] or '',
        'product_name': tp['name'] or '',
        'interest_rate_display': f"{tp['interest_rate']}%",
        'promotion': '',
        'features': [],
    } for tp in top_products]
    recommended_products_json = json.dumps(recommended_products, ensure_ascii=False)

    # 6) ส่ง context ไป template
    context = {
        'form': form,
        'user_properties': user_properties,
        'banks_with_stats': banks_with_stats,
        'pre_selected_loan_product_id': pre_selected_loan_product_id,
        'preselected_bank_ids': preselected_bank_ids,
        'properties_json': properties_json,
        'recommended_products_json': recommended_products_json,
    }
    return render(request, 'refinance/loan_application_form.html', context)

from django.db import transaction
@login_required
@login_required
def loan_application_update(request, pk):
    """แก้ไขใบสมัครสินเชื่อ"""
    try:
        application = get_object_or_404(LoanApplication, pk=pk, user=request.user)

        user_properties = Property.objects.filter(user=request.user)
        all_active_banks = Bank.objects.filter(is_active=True).order_by('name')

        if request.method == 'POST':
            form = LoanApplicationForm(request.POST, instance=application, user=request.user)
            if form.is_valid():
                with transaction.atomic():
                    app = form.save()

                    # ซิงก์ธนาคารกับ ApplicationBank
                    selected_banks = form.cleaned_data.get('selected_banks', [])
                    ApplicationBank.objects.filter(application=app).exclude(bank__in=selected_banks).delete()
                    for bank in selected_banks:
                        ApplicationBank.objects.get_or_create(
                            application=app,
                            bank=bank,
                            defaults={'status': 'submitted'}
                        )

                messages.success(request, 'ใบสมัครสินเชื่อถูกอัปเดตแล้ว!')
                try:
                    ActivityLog.objects.create(
                        user=request.user,
                        activity_type='profile_update',
                        description=f'อัปเดตใบสมัครสินเชื่อ: {application.application_no}'
                    )
                except Exception as log_error:
                    logger.error(f"Error creating activity log: {log_error}")

                return redirect('refinance:loan_application_detail', pk=pk)
        else:
            initial = {
                'selected_banks': application.application_banks.values_list('bank_id', flat=True)
            }
            form = LoanApplicationForm(instance=application, user=request.user, initial=initial)

        # สำหรับ template
        selected_ids = set(map(str, form['selected_banks'].value() or []))
        properties_json = _serialize_properties_for_frontend(user_properties)
        # แนะนำผลิตภัณฑ์อิงจากทรัพย์สินที่เลือกในฟอร์มตอนนี้
        current_property = form.initial.get('property') if isinstance(form.initial.get('property'), Property) else application.property
        recommended_products_json = _serialize_recommended_products(current_property)

        context = {
            'form': form,
            'user_properties': user_properties,
            'all_active_banks': all_active_banks,
            'preselected_bank_ids': selected_ids,
            'properties_json': properties_json,
            'recommended_products_json': recommended_products_json,
        }
        return render(request, 'refinance/loan_application_form.html', context)

    except LoanApplication.DoesNotExist:
        messages.error(request, "ไม่พบใบสมัครที่ต้องการแก้ไข")
        return redirect('refinance:loan_application_list')
    except Exception as e:
        logger.error(f"Error in loan_application_update: {e}", exc_info=True)
        messages.error(request, "เกิดข้อผิดพลาดในการแก้ไขใบสมัคร")
        return redirect('refinance:loan_application_list')

# ตรวจสอบว่ามี view นี้ใน refinance/views.py หรือไม่

@login_required
def loan_application_submit(request, pk):
    """ส่งใบสมัครสินเชื่อ"""
    try:
        application = get_object_or_404(LoanApplication, pk=pk, user=request.user)
        
        if request.method == 'POST':
            if application.status == 'draft':
                # เปลี่ยนสถานะจาก draft เป็น submitted
                application.status = 'submitted'
                application.submitted_at = timezone.now()
                application.save()

                messages.success(request, f'คำขอ "{application.application_no}" ถูกส่งเรียบร้อยแล้ว!')
                
                # บันทึก Activity Log
                try:
                    ActivityLog.objects.create(
                        user=request.user,
                        activity_type='loan_application',
                        description=f'ส่งใบสมัครสินเชื่อ: {application.application_no}'
                    )
                except Exception as log_error:
                    logger.error(f"Error creating activity log: {log_error}")
                
                return redirect('refinance:loan_application_detail', pk=pk)
            else:
                messages.warning(request, 'คำขอนี้ไม่สามารถส่งได้ในสถานะปัจจุบัน')
        
        return redirect('refinance:loan_application_detail', pk=pk)
        
    except LoanApplication.DoesNotExist:
        messages.error(request, "ไม่พบคำขอที่ต้องการ")
        return redirect('refinance:loan_application_list')
    except Exception as e:
        logger.error(f"Error in loan_application_submit: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการส่งคำขอ")
        return redirect('refinance:loan_application_list')
@login_required
def loan_application_delete(request, pk):
    """ลบใบสมัครสินเชื่อ"""
    try:
        application = get_object_or_404(LoanApplication, pk=pk, user=request.user)
        
        if request.method == 'POST':
            app_no = application.application_no
            application.delete()
            messages.success(request, f'ใบสมัคร "{app_no}" ถูกลบเรียบร้อยแล้ว!')
            
            # บันทึก Activity Log
            try:
                ActivityLog.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=f'ลบใบสมัครสินเชื่อ: {app_no}'
                )
            except Exception as log_error:
                logger.error(f"Error creating activity log: {log_error}")
            
            return redirect('refinance:loan_application_list')
        
        return render(request, 'refinance/loan_application_confirm_delete.html', {'application': application})
        
    except LoanApplication.DoesNotExist:
        messages.error(request, "ไม่พบใบสมัครที่ต้องการลบ")
        return redirect('refinance:loan_application_list')
    except Exception as e:
        logger.error(f"Error in loan_application_delete: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการลบใบสมัคร")
        return redirect('refinance:loan_application_list')

# --- Document Views ---

@login_required
def document_list(request):
    """รายการเอกสาร"""
    try:
        documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
        return render(request, 'refinance/document_list.html', {'documents': documents})
    except Exception as e:
        logger.error(f"Error in document_list: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายการเอกสาร")
        return render(request, 'refinance/document_list.html', {'documents': []})

# แทนที่ document_upload view ใน refinance/views.py

@login_required
def document_upload(request, application_pk=None):
    """อัปโหลดเอกสาร - รองรับหลายไฟล์"""
    try:
        # ดึง loan applications ของ user สำหรับ dropdown
        loan_applications = LoanApplication.objects.filter(user=request.user)
        
        application = None
        if application_pk:
            application = get_object_or_404(LoanApplication, pk=application_pk, user=request.user)

        if request.method == 'POST':
            print("POST request received")  # Debug
            print("FILES:", request.FILES)  # Debug
            print("POST data:", request.POST)  # Debug
            
            # ตรวจสอบข้อมูลที่จำเป็น
            title = request.POST.get('title', '').strip()
            document_type = request.POST.get('document_type', '').strip()
            description = request.POST.get('description', '').strip()
            
            if not title:
                messages.error(request, 'กรุณาระบุชื่อเอกสาร')
                context = {
                    'loan_applications': loan_applications,
                    'application_pk': application_pk,
                }
                return render(request, 'refinance/document_upload.html', context)
            
            if not document_type:
                messages.error(request, 'กรุณาเลือกประเภทเอกสาร')
                context = {
                    'loan_applications': loan_applications,
                    'application_pk': application_pk,
                }
                return render(request, 'refinance/document_upload.html', context)
            
            # ตรวจสอบไฟล์
            files = request.FILES.getlist('files')
            if not files:
                messages.error(request, 'กรุณาเลือกไฟล์ที่ต้องการอัปโหลด')
                context = {
                    'loan_applications': loan_applications,
                    'application_pk': application_pk,
                }
                return render(request, 'refinance/document_upload.html', context)
            
            print(f"Found {len(files)} files")  # Debug
            
            # ดึง loan application ถ้ามี
            loan_application = None
            loan_app_id = request.POST.get('loan_application')
            if loan_app_id and loan_app_id.strip():
                try:
                    loan_application = LoanApplication.objects.get(
                        id=loan_app_id, 
                        user=request.user
                    )
                except LoanApplication.DoesNotExist:
                    pass
            
            # ถ้ามี application_pk ให้ใช้เป็น default
            if application:
                loan_application = application
            
            # อัปโหลดไฟล์แต่ละไฟล์
            uploaded_count = 0
            for file in files:
                try:
                    # ตรวจสอบขนาดไฟล์ (10MB)
                    if file.size > 10 * 1024 * 1024:
                        messages.warning(request, f'ไฟล์ {file.name} มีขนาดใหญ่เกินไป (สูงสุด 10MB)')
                        continue
                    
                    # ตรวจสอบประเภทไฟล์
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                    import os
                    file_extension = os.path.splitext(file.name)[1].lower()
                    if file_extension not in allowed_extensions:
                        messages.warning(request, f'ไฟล์ {file.name} ไม่ใช่ประเภทที่รองรับ')
                        continue
                    
                    # สร้าง Document object โดยใช้ field ที่ถูกต้องตาม model
                    document = Document.objects.create(
                        user=request.user,
                        name=title if len(files) == 1 else f"{title} - {file.name}",  # ใช้ 'name' ตาม model
                        description=description,
                        document_type=document_type,
                        file=file,
                        application=loan_application  # ใช้ 'application' ตาม model
                    )
                    
                    print(f"Created document: {document.id} - {document.name}")  # Debug
                    uploaded_count += 1
                    
                    # บันทึก Activity Log
                    try:
                        ActivityLog.objects.create(
                            user=request.user,
                            activity_type='document_upload',
                            description=f'อัปโหลดเอกสาร: {document.name}'
                        )
                    except Exception as log_error:
                        logger.error(f"Error creating activity log: {log_error}")
                    
                except Exception as e:
                    print(f"Error uploading file {file.name}: {e}")  # Debug
                    messages.error(request, f'เกิดข้อผิดพลาดในการอัปโหลดไฟล์ {file.name}: {str(e)}')
            
            if uploaded_count > 0:
                if uploaded_count == 1:
                    messages.success(request, 'อัปโหลดเอกสารเรียบร้อยแล้ว')
                else:
                    messages.success(request, f'อัปโหลดเอกสารเรียบร้อยแล้ว {uploaded_count} ไฟล์')
                
                # Redirect ตามกรณี
                if application:
                    return redirect('refinance:loan_application_detail', pk=application.pk)
                return redirect('refinance:document_list')
            else:
                messages.error(request, 'ไม่สามารถอัปโหลดเอกสารได้')
        
        context = {
            'loan_applications': loan_applications,
            'application_pk': application_pk,
            'application': application,
        }
        return render(request, 'refinance/document_upload.html', context)
        
    except LoanApplication.DoesNotExist:
        messages.error(request, "ไม่พบใบสมัครที่ต้องการ")
        return redirect('refinance:loan_application_list')
    except Exception as e:
        print(f"General error in document_upload: {e}")  # Debug
        import traceback
        traceback.print_exc()
        messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
        return redirect('refinance:document_list')
    
# แทนที่ document_delete view ใน refinance/views.py

@login_required
def document_delete(request, pk):
    """ลบเอกสาร"""
    try:
        document = get_object_or_404(Document, pk=pk, user=request.user)
        
        if request.method == 'POST':
            doc_name = document.name  # ใช้ 'name' ตาม model
            application_pk = document.application.pk if document.application else None  # ใช้ 'application' ตาม model
            
            # ลบไฟล์จาก storage
            if document.file:
                try:
                    document.file.delete()
                except:
                    pass  # ไม่ให้ error ถ้าลบไฟล์ไม่ได้
            
            document.delete()
            
            messages.success(request, f'เอกสาร "{doc_name}" ถูกลบเรียบร้อยแล้ว!')
            
            # บันทึก Activity Log
            try:
                ActivityLog.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=f'ลบเอกสาร: {doc_name}'
                )
            except Exception as log_error:
                logger.error(f"Error creating activity log: {log_error}")
            
            if application_pk:
                return redirect('refinance:loan_application_detail', pk=application_pk)
            return redirect('refinance:document_list')
        
        return render(request, 'refinance/document_confirm_delete.html', {'document': document})
        
    except Document.DoesNotExist:
        messages.error(request, "ไม่พบเอกสารที่ต้องการลบ")
        return redirect('refinance:document_list')
    except Exception as e:
        logger.error(f"Error in document_delete: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการลบเอกสาร")
        return redirect('refinance:document_list')
# --- Public Views ---

def contact_us(request):
    """หน้าติดต่อเรา"""
    try:
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                name = cleaned_data['name']
                email = cleaned_data['email']
                phone = cleaned_data.get('phone', '')
                subject = cleaned_data['subject']
                message_text = cleaned_data['message']

                # บันทึก Activity Log
                try:
                    ActivityLog.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        activity_type='contact_us',
                        description=f'Contact Form Submission: Subject: {subject}, From: {name}',
                        details={'email': email, 'phone': phone, 'message': message_text}
                    )
                except Exception as log_error:
                    logger.error(f"Error creating contact activity log: {log_error}")
                
                messages.success(request, 'ข้อความของคุณถูกส่งเรียบร้อยแล้ว! เราจะติดต่อกลับโดยเร็วที่สุด')
                return redirect('refinance:contact_us')
        else:
            form = ContactForm()
        
        return render(request, 'refinance/contact_us.html', {'form': form})
        
    except Exception as e:
        logger.error(f"Error in contact_us: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการส่งข้อความ")
        return render(request, 'refinance/contact_us.html', {'form': ContactForm()})

def bank_list(request):
    """รายการธนาคาร พร้อมระบบค้นหาและกรอง"""
    try:
        # เริ่มต้นด้วย queryset ของธนาคารที่ active
        banks = Bank.objects.filter(is_active=True)

        # 1. กรองตามประเภทธนาคาร (bank_type)
        bank_type = request.GET.get('bank_type') # ดึงค่า bank_type จาก URL parameters
        if bank_type: # ถ้ามีค่า bank_type ส่งมา
            # สมมติว่า bank_type ในโมเดลเก็บเป็นค่าเดียวกับใน option value (e.g., 'government', 'private', 'foreign')
            banks = banks.filter(bank_type=bank_type)

        # 2. ค้นหาตามชื่อ (search)
        search_query = request.GET.get('search') # ดึงค่า search จาก URL parameters
        if search_query: # ถ้ามีค่า search ส่งมา
            # ค้นหาใน field 'name' ของธนาคาร โดยไม่สนใจตัวพิมพ์เล็กใหญ่ (icontains)
            # หากต้องการค้นหาในหลาย field (เช่น ชื่อหรือรหัส) สามารถใช้ Q objects ได้
            # ตัวอย่างเช่น:
            # banks = banks.filter(Q(name__icontains=search_query) | Q(code__icontains=search_query))
            banks = banks.filter(name__icontains=search_query) # ค้นหาเฉพาะชื่อธนาคาร

        # เรียงลำดับตาม display_order และ name (ให้คงไว้ท้ายสุดหลังจากกรอง)
        banks = banks.order_by('display_order', 'name')

        context = {
            'banks': banks
        }
        return render(request, 'refinance/bank_list.html', context)

    except Exception as e:
        # ควรใช้ logger.error แทน print ใน production เพื่อบันทึกข้อผิดพลาด
        logger.error(f"Error in bank_list view: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายการธนาคาร")
        return render(request, 'refinance/bank_list.html', {'banks': []})

def bank_detail(request, pk):
    """รายละเอียดธนาคาร"""
    try:
        bank = get_object_or_404(Bank, pk=pk, is_active=True)
        loan_products = bank.loan_products.filter(is_active=True).order_by('display_order', 'name')
        
        # ดึงโปรโมชั่น
        promotions = []
        try:
            if hasattr(bank, 'get_active_promotions'):
                promotions = bank.get_active_promotions()
            else:
                promotions = bank.promotions.filter(
                    is_active=True,
                    start_date__lte=timezone.now().date(),
                    end_date__gte=timezone.now().date()
                )
        except Exception as promo_error:
            logger.error(f"Error getting promotions for bank {bank.name}: {promo_error}")
        
        # ดึงค่าธรรมเนียม
        fees = []
        try:
            fees = bank.fees.filter(is_active=True).select_related('fee_type')
        except Exception as fee_error:
            logger.error(f"Error getting fees for bank {bank.name}: {fee_error}")
        
        context = {
            'bank': bank,
            'loan_products': loan_products,
            'promotions': promotions,
            'fees': fees,
        }
        return render(request, 'refinance/bank_detail.html', context)
        
    except Bank.DoesNotExist:
        messages.error(request, "ไม่พบธนาคารที่ต้องการ")
        return redirect('refinance:bank_list')
    except Exception as e:
        logger.error(f"Error in bank_detail: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายละเอียดธนาคาร")
        return redirect('refinance:bank_list')

def loan_product_list(request):
    """รายการผลิตภัณฑ์สินเชื่อ"""
    try:
        products = LoanProduct.objects.filter(is_active=True).select_related('bank')
        
        # กรองตามพารามิเตอร์
        bank_id = request.GET.get('bank')
        product_type = request.GET.get('product_type')
        
        if bank_id:
            try:
                products = products.filter(bank__id=int(bank_id))
            except (ValueError, TypeError):
                pass

        if product_type:
            products = products.filter(product_type=product_type)

        # ดึงข้อมูลสำหรับ dropdown
        banks = Bank.objects.filter(is_active=True).order_by('name')
        product_types = LoanProduct.PRODUCT_TYPE_CHOICES if hasattr(LoanProduct, 'PRODUCT_TYPE_CHOICES') else []

        context = {
            'products': products,
            'banks': banks,
            'product_types': product_types,
            'selected_bank': bank_id,
            'selected_product_type': product_type,
        }
        return render(request, 'refinance/loan_product_list.html', context)

    except Exception as e:
        logger.error(f"Error in loan_product_list: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายการผลิตภัณฑ์")
        return render(request, 'refinance/loan_product_list.html', {
            'products': [],
            'banks': [],
            'product_types': [],
        })

def loan_product_detail(request, pk):
    """รายละเอียดผลิตภัณฑ์สินเชื่อ"""
    try:
        product = get_object_or_404(LoanProduct, pk=pk, is_active=True)
        
        # ดึงประวัติอัตราดอกเบี้ย
        rate_history = []
        try:
            if hasattr(product, 'rate_history'):
                rate_history = product.rate_history.order_by('-effective_date')[:5]
        except Exception as history_error:
            logger.error(f"Error getting rate history: {history_error}")
        
        context = {
            'product': product,
            'rate_history': rate_history,
        }
        return render(request, 'refinance/loan_product_detail.html', context)
        
    except LoanProduct.DoesNotExist:
        messages.error(request, "ไม่พบผลิตภัณฑ์ที่ต้องการ")
        return redirect('refinance:loan_product_list')
    except Exception as e:
        logger.error(f"Error in loan_product_detail: {e}")
        messages.error(request, "เกิดข้อผิดพลาดในการโหลดรายละเอียดผลิตภัณฑ์")
        return redirect('refinance:loan_product_list')

# --- API Views ---

def search_banks_api(request):
    """API สำหรับค้นหาธนาคาร"""
    try:
        query = request.GET.get('q', '').strip()
        banks = Bank.objects.filter(is_active=True)
        
        if query:
            banks = banks.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
        
        banks = banks.order_by('name')[:20]  # จำกัดผลลัพธ์
        
        results = []
        for bank in banks:
            try:
                results.append({
                    'id': bank.id,
                    'name': bank.name,
                    'code': getattr(bank, 'code', ''),
                })
            except Exception as bank_error:
                logger.error(f"Error processing bank {bank.id}: {bank_error}")
                continue
        
        return JsonResponse(results, safe=False)
        
    except Exception as e:
        logger.error(f"Error in search_banks_api: {e}")
        return JsonResponse({'error': 'เกิดข้อผิดพลาดในการค้นหา'}, status=500)

def search_loan_products_api(request):
    """API สำหรับค้นหาผลิตภัณฑ์สินเชื่อ"""
    try:
        query = request.GET.get('q', '').strip()
        product_type = request.GET.get('product_type', '').strip()
        bank_id = request.GET.get('bank_id', '').strip()

        products = LoanProduct.objects.filter(is_active=True).select_related('bank')

        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(bank__name__icontains=query)
            )
        
        if product_type:
            products = products.filter(product_type=product_type)
        
        if bank_id:
            try:
                products = products.filter(bank__id=int(bank_id))
            except (ValueError, TypeError):
                pass

        products = products.order_by('bank__name', 'name')[:20]  # จำกัดผลลัพธ์

        results = []
        for product in products:
            try:
                results.append({
                    'id': product.id,
                    'name': f"{product.bank.name} - {product.name}",
                    'bank_name': product.bank.name,
                    'interest_rate': float(product.interest_rate),
                    'product_type': getattr(product, 'product_type', ''),
                })
            except Exception as product_error:
                logger.error(f"Error processing product {product.id}: {product_error}")
                continue

        return JsonResponse(results, safe=False)
        
    except Exception as e:
        logger.error(f"Error in search_loan_products_api: {e}")
        return JsonResponse({'error': 'เกิดข้อผิดพลาดในการค้นหา'}, status=500)

# --- Utility Functions ---

def _safe_decimal_conversion(value, default=Decimal('0.00')):
    """แปลงค่าเป็น Decimal อย่างปลอดภัย"""
    try:
        if value is None:
            return default
        return Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        return default

def _safe_int_conversion(value, default=0):
    """แปลงค่าเป็น int อย่างปลอดภัย"""
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def _safe_get_attr(obj, attr_name, default=None):
    """ดึง attribute อย่างปลอดภัย"""
    try:
        return getattr(obj, attr_name, default)
    except AttributeError:
        return default

def _calculate_monthly_payment_pmt(principal, annual_rate, years):
    """
    คำนวณค่าผ่อนรายเดือนด้วยสูตร PMT (Payment)
    สูตรที่แม่นยำกว่าการคำนวณแบบง่าย
    """
    try:
        if principal <= 0 or years <= 0:
            return Decimal('0.00')
        
        if annual_rate <= 0:
            # กรณีดอกเบี้ย 0%
            return (principal / (years * 12)).quantize(Decimal('0.01'))
        
        monthly_rate = annual_rate / 100 / 12
        num_payments = years * 12
        
        # สูตร PMT: P * [r(1+r)^n] / [(1+r)^n - 1]
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        
        return Decimal(str(monthly_payment)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    except Exception as e:
        logger.error(f"Error calculating monthly payment: {e}")
        return Decimal('0.00')

def _log_user_activity(user, activity_type, description, details=None):
    """บันทึก Activity Log อย่างปลอดภัย"""
    try:
        ActivityLog.objects.create(
            user=user if user and user.is_authenticated else None,
            activity_type=activity_type,
            description=description,
            details=details or {}
        )
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")

# --- Error Handlers ---

def handle_404(request, exception):
    """จัดการหน้า 404"""
    return render(request, 'refinance/404.html', status=404)

def handle_500(request):
    """จัดการหน้า 500"""
    return render(request, 'refinance/500.html', status=500)

# --- Health Check ---

def health_check(request):
    """ตรวจสอบสถานะระบบ"""
    try:
        # ตรวจสอบการเชื่อมต่อ database
        Bank.objects.exists()

        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@login_required
def property_add(request):
    """
    View สำหรับเพิ่มข้อมูลทรัพย์สินใหม่
    """
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_instance = form.save(commit=False)
            property_instance.user = request.user
            property_instance.save()
            messages.success(request, 'เพิ่มข้อมูลทรัพย์สินสำเร็จแล้ว!')
            return redirect('refinance:property_list')
        else:
            messages.error(request, 'เกิดข้อผิดพลาดในการบันทึกข้อมูลทรัพย์สิน กรุณาตรวจสอบอีกครั้ง')
    else:
        form = PropertyForm()
    
    return render(request, 'refinance/add_prop.html', {'form': form})


def faq_view(request):
    """
    Renders the FAQ page.
    """
    return render(request, 'refinance/faq.html')

from django.shortcuts import render, get_object_or_404
from .models import Article  # นำเข้าโมเดล Article

# ... (ฟังก์ชันที่มีอยู่เดิม)

def article_list_view(request):
    """
    Renders the articles page with a list of articles from the database.
    """
    articles = Article.objects.all()
    return render(request, 'refinance/articles.html', {'articles': articles})

def article_detail_view(request, slug):
    """
    Renders a single article page.
    """
    article = get_object_or_404(Article, slug=slug)
    return render(request, 'refinance/article_detail.html', {'article': article})


def _serialize_properties_for_frontend(properties):
    data = {}
    for p in properties:
        try:
            data[str(p.id)] = {
                'type': getattr(p, 'property_type', '') or '',
                'value': float(p.estimated_value) if getattr(p, 'estimated_value', None) else 0,
                'province': getattr(getattr(p, 'province', None), 'name', '') or '',
                'current_debt': float(p.existing_loan_balance) if getattr(p, 'existing_loan_balance', None) else 0,
                'current_bank': getattr(getattr(p, 'existing_bank', None), 'name', '') or '',
                'ltv': round(
                    (float(p.existing_loan_balance) / float(p.estimated_value) * 100.0)
                    if getattr(p, 'existing_loan_balance', None) and getattr(p, 'estimated_value', None) and float(p.estimated_value) > 0
                    else 0.0,
                    1
                ),
            }
        except Exception:
            data[str(p.id)] = {
                'type': '',
                'value': 0,
                'province': '',
                'current_debt': 0,
                'current_bank': '',
                'ltv': 0.0,
            }
    return json.dumps(data, ensure_ascii=False)

def _serialize_recommended_products(property_obj=None, limit=6):
    """
    ดึง LoanProduct จากฐานข้อมูลจริง (ไม่ mock) สำหรับแสดงแนะนำเบื้องต้น
    ถ้ามี property_obj จะสามารถกรองเบื้องต้นได้ตามเงื่อนไขง่ายๆ เช่น product_type='refinance'
    """
    qs = LoanProduct.objects.filter(is_active=True).select_related('bank')

    # กรองพื้นฐานสำหรับรีไฟแนนซ์
    qs = qs.filter(product_type='refinance')

    # ถ้ามีข้อมูลทรัพย์สิน จะกรองเบาๆ ตามวงเงิน/รายได้ได้ (ถ้าฟิลด์ในโมเดลรองรับ)
    if property_obj:
        try:
            loan_balance = getattr(property_obj, 'existing_loan_balance', None)
            if loan_balance:
                qs = qs.filter(min_loan_amount__lte=loan_balance)
        except Exception:
            pass

    qs = qs.order_by('interest_rate')[:limit]

    items = []
    for prod in qs:
        items.append({
            'id': prod.id,
            'bank_name': prod.bank.name if prod.bank else '',
            'product_name': prod.name,
            'interest_rate_display': f"{prod.interest_rate}%",
            'promotion': getattr(getattr(prod, 'bank', None), 'promotion_title', '') or '',
            'features': [],  # ถ้ามีฟิลด์ features ค่อยเติม
        })
    return json.dumps(items, ensure_ascii=False)
