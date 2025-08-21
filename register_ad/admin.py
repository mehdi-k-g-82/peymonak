from django.contrib import admin

from .models import Register_Request, register_ad, Report_Register_Request, RegisterAdImage

admin.site.register(Register_Request)
admin.site.register(register_ad)
admin.site.register(Report_Register_Request)
admin.site.register(RegisterAdImage)