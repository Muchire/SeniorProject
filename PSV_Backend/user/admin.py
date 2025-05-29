from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_passenger', 'is_vehicle_owner', 'is_sacco_admin', 'sacco_admin_requested']
    list_filter = ['is_passenger', 'is_vehicle_owner', 'is_sacco_admin', 'sacco_admin_requested']

admin.site.register(User, UserAdmin)
