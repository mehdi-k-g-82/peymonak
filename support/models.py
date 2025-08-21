from django.db import models


class SupportRequest(models.Model):
    email = models.EmailField(max_length=100)
    telegram_link = models.URLField(max_length=250)
    eitaa_link = models.URLField(max_length=250)
