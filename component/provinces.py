import os
from django.conf import settings

PROVINCE_FILE_PATH = os.path.join(
    settings.BASE_DIR,
    'provinces/province_name_list/provinces.txt'
)

PROVINCES = []

try:
    with open(PROVINCE_FILE_PATH, 'r', encoding='utf-8') as f:
        # تبدیل هر خط به تاپل دوتایی (value, label)
        PROVINCES = [(line.strip(), line.strip()) for line in f if line.strip()]

except FileNotFoundError:
    raise RuntimeError(
        f"فایل استانها در مسیر '{PROVINCE_FILE_PATH}' یافت نشد! "
        "لطفا از درستی مسیر اطمینان حاصل کنید."
    )
except Exception as e:
    raise RuntimeError(f"خطای غیرمنتظره در پردازش فایل: {str(e)}")