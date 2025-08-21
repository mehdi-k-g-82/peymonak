from django.db import models
from django.conf import settings
from django.utils import timezone
from component.provinces import PROVINCES
from component.skill import SKILL
from component.gender import GENDER_CHOICES

COOPERATION_KIND = [
    ('فرد', 'فرد'),
    ('شرکت', 'شرکت')
]

STATUS_CHOICES = [
    ('active', 'فعال'),
    ('inactive', 'غیرفعال')
]


class register_ad(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, editable=False)
    selected_professional = models.CharField(max_length=30)
    title = models.CharField(max_length=38)
    description = models.TextField()
    gender = models.CharField(choices=GENDER_CHOICES, max_length=3, editable=False)
    fee = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20, editable=False)
    province = models.CharField(max_length=30, choices=PROVINCES)
    city = models.CharField(max_length=45, choices=PROVINCES)
    cooperation_kind = models.CharField(max_length=25, choices=COOPERATION_KIND, null=True, blank=True)
    skill = models.CharField(max_length=45, choices=SKILL, null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'ad'

    def __str__(self):
        return self.title


class Register_Request(models.Model):
    ad = models.ForeignKey(register_ad, on_delete=models.CASCADE)
    sender_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_requests', on_delete=models.CASCADE)
    recipient_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_requests',
                                       on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    is_pending = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(default=timezone.now)
    is_accepted = models.BooleanField(default=False)
    sender_phone = models.CharField(max_length=15, blank=True, null=True)
    recipient_phone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        unique_together = ('ad', 'sender_user')
        db_table = 'register_request'


class Report_Register_Request(models.Model):
    ad = models.ForeignKey(register_ad, on_delete=models.CASCADE)
    sender_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reporter_user', on_delete=models.CASCADE)
    message = models.CharField(max_length=1500)

    def __str__(self):
        return f'reporter:{self.sender_user} | message:{self.message}'


class RegisterAdImage(models.Model):
    register_ad = models.ForeignKey(register_ad, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/register-ad/', null=True, blank=True)

    def __str__(self):
        return f"Image for {self.register_ad.title}"
