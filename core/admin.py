from django.contrib import admin

from .models import CustomUser,AbstractUser

admin.site.register(CustomUser)
# admin.site.register(AbstractUser)
