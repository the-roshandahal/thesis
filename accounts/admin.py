from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


admin.site.register(Admin)
admin.site.register(Supervisor)
admin.site.register(Student)
admin.site.register(User, BaseUserAdmin)