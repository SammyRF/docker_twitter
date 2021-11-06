from django.contrib import admin
from tweets.models import Tweet, TweetPhoto

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'id',
        'created_at',
        'user',
        'content',
    )


@admin.register(TweetPhoto)
class TweetPhotoAdmin(admin.ModelAdmin):
    list_display = (
        'tweet',
        'user',
        'file',
        'status',
        'is_deleted',
        'created_at',
    )
    list_filter = ('status', 'is_deleted')
    date_hierarchy = 'created_at'
