# refinance/management/commands/update_interest_rates.py
# คำสั่งสำหรับอัปเดตอัตราดอกเบี้ยปัจจุบัน

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from refinance.models import Bank, LoanProduct, InterestRateHistory
import random

class Command(BaseCommand):
    help = 'Update current interest rates for all banks and loan products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bank-code',
            type=str,
            help='Update rates for specific bank only (e.g., BBL, SCB)',
        )
        parser.add_argument(
            '--rate-change',
            type=float,
            default=0.0,
            help='Apply rate change to all products (e.g., +0.25, -0.15)',
        )
        parser.add_argument(
            '--simulate-market',
            action='store_true',
            help='Simulate market rate changes with random variations',
        )

    def handle(self, *args, **options):
        bank_code = options.get('bank_code')
        rate_change = Decimal(str(options.get('rate_change', 0.0)))
        simulate_market = options.get('simulate_market', False)

        # กรองธนาคารตามเงื่อนไข
        banks = Bank.objects.filter(is_active=True)
        if bank_code:
            banks = banks.filter(code__iexact=bank_code)
            if not banks.exists():
                self.stdout.write(
                    self.style.ERROR(f'Bank with code "{bank_code}" not found')
                )
                return

        self.stdout.write(f'Updating interest rates for {banks.count()} banks...')

        for bank in banks:
            self.update_bank_rates(bank, rate_change, simulate_market)

        self.stdout.write(
            self.style.SUCCESS('Successfully updated interest rates')
        )

    def update_bank_rates(self, bank, rate_change, simulate_market):
        """อัปเดตอัตราดอกเบี้ยสำหรับธนาคาร"""
        
        loan_products = bank.loan_products.filter(is_active=True)
        
        for product in loan_products:
            old_rate = product.interest_rate
            
            if simulate_market:
                # จำลองการเปลี่ยนแปลงของตลาด
                market_change = Decimal(str(random.uniform(-0.3, 0.3)))
                new_rate = old_rate + market_change
            else:
                # ใช้การเปลี่ยนแปลงที่กำหนด
                new_rate = old_rate + rate_change
            
            # จำกัดอัตราไม่ให้ต่ำเกินไปหรือสูงเกินไป
            new_rate = max(Decimal('1.50'), min(new_rate, Decimal('8.00')))
            
            # อัปเดตอัตราดอกเบี้ย
            product.interest_rate = new_rate
            product.save()
            
            # บันทึกประวัติ
            InterestRateHistory.objects.create(
                bank=bank,
                loan_product=product,
                interest_rate=new_rate,
                effective_date=timezone.now().date(),
                notes=f'Updated from {old_rate}% to {new_rate}%'
            )
            
            change_direction = "↑" if new_rate > old_rate else "↓" if new_rate < old_rate else "→"
            self.stdout.write(
                f'  {bank.name} - {product.name}: '
                f'{old_rate}% {change_direction} {new_rate}%'
            )

class Command(BaseCommand):
    help = 'Generate realistic bank promotion campaigns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--season',
            type=str,
            choices=['new-year', 'mid-year', 'year-end', 'general'],
            default='general',
            help='Generate promotions for specific season',
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Promotion duration in days',
        )

    def handle(self, *args, **options):
        from refinance.models import Promotion
        from datetime import timedelta
        
        season = options.get('season')
        duration = options.get('duration')
        current_date = timezone.now().date()
        
        # กำหนดชื่อโปรโมชั่นตามฤดูกาล
        season_campaigns = {
            'new-year': {
                'prefix': 'โปรโมชั่นต้นปี',
                'special_rate': Decimal('1.99'),
                'cashback_multiplier': 1.5
            },
            'mid-year': {
                'prefix': 'โปรโมชั่นกลางปี',
                'special_rate': Decimal('2.29'),
                'cashback_multiplier': 1.2
            },
            'year-end': {
                'prefix': 'โปรโมชั่นปลายปี',
                'special_rate': Decimal('1.89'),
                'cashback_multiplier': 2.0
            },
            'general': {
                'prefix': 'โปรโมชั่นพิเศษ',
                'special_rate': Decimal('2.19'),
                'cashback_multiplier': 1.0
            }
        }
        
        campaign = season_campaigns[season]
        
        # ลบโปรโมชั่นเก่าที่หมดอายุ
        Promotion.objects.filter(
            end_date__lt=current_date,
            is_active=True
        ).update(is_active=False)
        
        banks = Bank.objects.filter(is_active=True, is_featured=True)
        
        for bank in banks:
            # สร้างโปรโมชั่นใหม่
            promo_title = f'{campaign["prefix"]} {bank.name} 2025'
            
            promotion = Promotion.objects.create(
                bank=bank,
                title=promo_title,
                description=f'อัตราพิเศษ {campaign["special_rate"]}% และสิทธิประโยชน์มากมาย',
                promotion_type='special_rate',
                min_loan_amount=Decimal('1000000'),
                max_loan_amount=Decimal('100000000'),
                special_rate=campaign['special_rate'],
                special_rate_period=12,
                start_date=current_date,
                end_date=current_date + timedelta(days=duration),
                is_active=True,
                is_sponsored=True,
                priority=20,
                terms_conditions=f'เงื่อนไข: {promo_title} ใช้ได้ถึง {(current_date + timedelta(days=duration)).strftime("%d/%m/%Y")}'
            )
            
            self.stdout.write(f'Created promotion: {promotion.title}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {season} season promotions')
        )