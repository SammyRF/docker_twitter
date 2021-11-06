from django.contrib import admin
from accounts.models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'nickname', 'avatar', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
