from django.core.management.base import BaseCommand
from refinance.models import Province # แก้ refinance เป็นชื่อ app ของคุณถ้าต่างกัน

class Command(BaseCommand):
    help = 'Populates the database with 77 provinces of Thailand.'

    def handle(self, *args, **kwargs):
        provinces = [
            "กรุงเทพมหานคร", "กระบี่", "กาญจนบุรี", "กาฬสินธุ์", "กำแพงเพชร",
            "ขอนแก่น", "จันทบุรี", "ฉะเชิงเทรา", "ชลบุรี", "ชัยนาท",
            "ชัยภูมิ", "ชุมพร", "เชียงราย", "เชียงใหม่", "ตรัง",
            "ตราด", "ตาก", "นครนายก", "นครปฐม", "นครพนม",
            "นครราชสีมา", "นครศรีธรรมราช", "นครสวรรค์", "นนทบุรี", "นราธิวาส",
            "น่าน", "บึงกาฬ", "บุรีรัมย์", "ปทุมธานี", "ประจวบคีรีขันธ์",
            "ปราจีนบุรี", "ปัตตานี", "พระนครศรีอยุธยา", "พะเยา", "พังงา",
            "พัทลุง", "พิจิตร", "พิษณุโลก", "เพชรบุรี", "เพชรบูรณ์",
            "แพร่", "ภูเก็ต", "มหาสารคาม", "มุกดาหาร", "แม่ฮ่องสอน",
            "ยโสธร", "ยะลา", "ร้อยเอ็ด", "ระนอง", "ระยอง",
            "ราชบุรี", "ลพบุรี", "ลำปาง", "ลำพูน", "เลย",
            "ศรีสะเกษ", "สกลนคร", "สงขลา", "สตูล", "สมุทรปราการ",
            "สมุทรสงคราม", "สมุทรสาคร", "สระแก้ว", "สระบุรี", "สิงห์บุรี",
            "สุโขทัย", "สุพรรณบุรี", "สุราษฎร์ธานี", "สุรินทร์", "หนองคาย",
            "หนองบัวลำภู", "อ่างทอง", "อำนาจเจริญ", "อุดรธานี", "อุตรดิตถ์",
            "อุทัยธานี", "อุบลราชธานี"
        ]

        # Add a default empty option, though it's handled by empty_label in form
        # if not Province.objects.filter(name='--- โปรดเลือก ---').exists():
        #     Province.objects.create(name='--- โปรดเลือก ---', is_active=True)

        for province_name in provinces:
            obj, created = Province.objects.get_or_create(
                name=province_name,
                defaults={'is_active': True} # ตรวจสอบให้แน่ใจว่า is_active เป็น True
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created province: {province_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Province already exists: {province_name}'))
                # If it exists, ensure is_active is True
                if not obj.is_active:
                    obj.is_active = True
                    obj.save()
                    self.stdout.write(self.style.SUCCESS(f'Activated province: {province_name}'))


        self.stdout.write(self.style.SUCCESS('Finished populating provinces.'))