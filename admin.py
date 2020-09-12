from django.contrib import admin

from .models import *

# Register your models here.
class VideoSyncPodcastAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'user', 'related_podcast_object', )
    search_fields = ['name', ]
admin.site.register(VideoSyncPodcast, VideoSyncPodcastAdmin)

class VideoSyncEpisodeAdmin(admin.ModelAdmin):
    list_display = ('text', 'podcast', 'create_time', )
    search_fields = ['podcast']
admin.site.register(VideoSyncEpisode, VideoSyncEpisodeAdmin)
