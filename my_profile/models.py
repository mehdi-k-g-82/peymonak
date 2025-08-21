from component.provinces import PROVINCES
from django.db import models
from component.gender import GENDER_CHOICES
from django.conf import settings
from component.skill import SKILL

from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='worker_profile')
    name = models.CharField(max_length=100)
    # last_name = models.CharField(max_length=30)
    city = models.CharField(max_length=100, choices=PROVINCES)
    gender = models.CharField(max_length=40, choices=GENDER_CHOICES)
    skill = models.CharField(max_length=50, choices=SKILL, null=True, blank=True)
    description = models.TextField()
    profile_picture = models.ImageField(upload_to='profile/picture/', null=True, blank=True)

    def __str__(self):
        return f"{self.name}'s Profile"

class Sample_image(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='samples')
    image = models.ImageField(upload_to='profile/sample/', null=True, blank=True)
