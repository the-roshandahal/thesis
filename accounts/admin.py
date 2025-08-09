from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('address',)}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('address',)}),
    )

class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'department', 'user_email', 'user_first_name', 'user_last_name')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'student_id')
    list_filter = ('department',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.short_description = 'First Name'
    
    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.short_description = 'Last Name'

class SupervisorAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_id', 'department', 'user_email', 'user_first_name', 'user_last_name')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'staff_id')
    list_filter = ('department',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.short_description = 'First Name'
    
    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.short_description = 'Last Name'

class AdminAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_id', 'user_email', 'user_first_name', 'user_last_name')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'staff_id')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.short_description = 'First Name'
    
    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.short_description = 'Last Name'

admin.site.register(Admin, AdminAdmin)
admin.site.register(Supervisor, SupervisorAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(User, CustomUserAdmin)