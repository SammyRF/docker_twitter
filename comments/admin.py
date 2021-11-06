from django.contrib import admin
from comments.models import Comment

@admin.register(Comment)
class TweetAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'id',
        'created_at',
        'user',
        'tweet',
        'content',
        'updated_at',
    )
