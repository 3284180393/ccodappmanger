from django.contrib import admin
from app_base.models import AppTemplate, Server, ServerUser, AppCfg, AppPriStbyCfg

# Register your models here.
admin.site.register(AppTemplate)
admin.site.register(Server)
admin.site.register(ServerUser)
admin.site.register(AppCfg)
admin.site.register(AppPriStbyCfg)
