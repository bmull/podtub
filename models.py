import os
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.urls import reverse
from s3direct.fields import S3DirectField
from colorfield.fields import ColorField

from dashboard.helper_slug import make_slug
from dashboard.models import Podcast, Episode

from redwoodlabs.helpers import generate_random_id

class YouTubeAccount(models.Model):
    email = models.EmailField(max_length=128, unique=True)
    youtube_id = models.CharField(max_length=128, unique=True)
    access_token = models.CharField(max_length=256, null=True, blank=True)
    refresh_token = models.CharField(max_length=256, null=True, blank=True)

class VideoSyncPodcast(models.Model):

    id = models.BigIntegerField(default=generate_random_id, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)

    image_path = S3DirectField(dest='images', null=True, blank=True,
        verbose_name='Podcast Artwork',
        help_text='The cover image that shows on Apple Podcasts, etc...')
    primary_color = ColorField(null=True, blank=True,
        help_text='Highlight color in images. Example: #333333')
    secondary_color = ColorField(null=True, blank=True, default='#FFFFFF',
        help_text='Alternative color in images. Example: #FFFFFF')
    logo_path = S3DirectField(dest='images', null=True, blank=True,
        verbose_name='Podcast Logo',
        help_text='Optional, but can be used for artwork.')
    font_name = models.CharField(max_length=200, null=True, blank=True,
        verbose_name='Font',
        help_text='Enter the name of any font from fonts.google.com.')

    default_template = models.CharField(max_length=100, null=True, blank=True,
        help_text='This is the default template used for new episodes')

    youtube_account = models.ForeignKey(YouTubeAccount, on_delete=models.SET_NULL, null=True, blank=True)
    youtube_channel_id = models.CharField(max_length=100, null=True, blank=True)
    youtube_channel_name = models.CharField(max_length=100, null=True, blank=True)

    blur_image_path = models.URLField(max_length=500, null=True, blank=True)

    related_podcast_object = models.OneToOneField(Podcast, on_delete=models.CASCADE, null=True, blank=True)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = make_slug(self)
        super().save(*args, **kwargs)

    def get_episodes(self):
        return self.videosyncepisode_set.all()

    def get_absolute_url(self):
        return reverse('videosync_episode_list_page', kwargs={'slug':self.slug})

    def get_edit_url(self):
        return reverse('videosync_podcast_update_page', kwargs={'slug':self.slug})

    @property
    def custom_font(self):
        font = None
        if self.font_name:
            font = {'param': self.font_name.replace(' ', '+'),'name': self.font_name }
        return font

    @property
    def youtube_connected(self):
        if self.youtube_account:
            return (self.youtube_account.access_token and self.youtube_account.refresh_token)
        return False

    @property
    def youtube_access_token(self):
        if self.youtube_account:
            return self.youtube_account.access_token
        return None

    @property
    def youtube_refresh_token(self):
        if self.youtube_account:
            return self.youtube_account.refresh_token
        return None


class VideoSyncEpisode(models.Model):

    IN_PROGRESS = 'P'
    SUCCESS = 'S'
    FAILED = 'F'
    UPLOAD_STATUS_CHOICES = (
        (IN_PROGRESS, 'In Progress'),
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
    )

    id = models.BigIntegerField(default=generate_random_id, primary_key=True)
    podcast = models.ForeignKey(VideoSyncPodcast, on_delete=models.CASCADE)

    text = models.CharField(max_length=250, null=True, blank=True)
    season = models.IntegerField(null=True, blank=True,
        verbose_name='Season Number',
        help_text='Leave blank if your podcast does not have seasons')
    number = models.IntegerField(null=True, blank=True,
        verbose_name='Episode Number')
    image_path = S3DirectField(dest='images', null=True, blank=True,
        verbose_name='Episode Image',
        help_text='Photo of guest, or drawing, or other graphic')

    template = models.CharField(max_length=100, null=True, blank=True)

    related_episode_object = models.OneToOneField(Episode, on_delete=models.CASCADE, null=True, blank=True)

    artwork_path = models.URLField(max_length=500, null=True, blank=True)
    audio_path = models.URLField(max_length=500, null=True, blank=True)
    preview_path = models.URLField(max_length=500, null=True, blank=True)
    video_path = models.URLField(max_length=500, null=True, blank=True)

    upload_status = models.CharField(max_length=1, choices=UPLOAD_STATUS_CHOICES, null=True, blank=True)
    sync_status = JSONField(blank=True, null=True)
    youtube_id = models.CharField(max_length=500, null=True, blank=True)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['-related_episode_object__published']

    def get_absolute_url(self):
        return reverse('videosync_episode_templates_page', kwargs={'podcast_slug':self.podcast.slug, 'pk': self.pk})

    def get_edit_url(self):
        return reverse('videosync_episode_update_page', kwargs={'podcast_slug':self.podcast.slug, 'pk': self.pk})

    @property
    def image(self):
        if self.image_path:
            return self.image_path
        else:
            return 'https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1502&q=80'

    @property
    def video_location(self):
        path = os.path.join('media', str(self.podcast.related_podcast_object.user.pk), str(self.podcast.related_podcast_object.pk), str(self.related_episode_object.id) + '.mp4')
        if os.path.exists(path):
            return path
        return None


    @property
    def youtube_url(self):
        if self.youtube_id:
            return "https://www.youtube.com/watch?v=" + self.youtube_id
        return None

    @property
    def youtube_embed_url(self):
        if self.youtube_id:
            return "https://www.youtube.com/embed/" + self.youtube_id
        return None

    @property
    def card_graphic(self):
        if self.youtube_embed_url:
            return '<div class="embed-container"><iframe src="%s" frameborder="0" allowfullscreen></iframe></div>' % self.youtube_embed_url
        elif self.artwork_path:
            return '<img src="%s">' % self.artwork_path
        return None

    def update_sync_status(self, event):
        sync_status = []
        if self.sync_status:
            self.sync_status.append(event)
            sync_status = self.sync_status
        else:
            sync_status = [event]

        self.sync_status = sync_status
        self.save()


