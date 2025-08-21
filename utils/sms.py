import requests
import logging

# تنظیم لاگ برای دیباگ
logger = logging.getLogger(__name__)


def send_verification_sms(phone_number, code):
    api_key = "34673075556F7669507A552F5A6F616B37676C2F6E6364346F784D396D7777474E796C784C76763577346B3D"  # کلید API کاوه‌نگار رو اینجا بذار
    url = f"https://api.kavenegar.com/v1/{api_key}/sms/send.json"

    # مطمئن شو که شماره با 09 شروع می‌شه
    if not phone_number.startswith("09"):
        phone_number = "0" + phone_number.lstrip("+98")

    payload = {
        "receptor": phone_number,
        "message": f"کد تأیید شما: {code}"
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        logger.info(f"درخواست به کاوه‌نگار: {payload}")
        logger.info(f"پاسخ کاوه‌نگار: {response.status_code} - {response.text}")

        if response.status_code == 200:
            return True
        else:
            error_message = response.json().get("return", {}).get("message", "خطای ناشناخته")
            raise Exception(f"خطا در ارسال پیامک: {response.status_code} - {error_message}")

    except requests.exceptions.RequestException as e:
        logger.error(f"خطا در اتصال به کاوه‌نگار: {str(e)}")
        raise Exception(f"خطا در اتصال به کاوه‌نگار: {str(e)}")