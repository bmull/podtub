from __future__ import absolute_import, unicode_literals

import io
import arrow
import requests

from django.core.mail import send_mail
from django.conf import settings

from celery import shared_task
from PIL import Image, ImageEnhance, ImageFilter

from identity.strings import GLOBAL_STRINGS
from videosync.models import VideoSyncEpisode, VideoSyncPodcast
from videosync.utils import GoogleClient, PodcastConverter, S3Service, S3Image
from showpage.celery import app

@app.task
def create_video(episode_id):
    episode = VideoSyncEpisode.objects.get(pk=episode_id)
    convert = PodcastConverter(episode)
    convert.create_video()

@app.task
def create_preview(episode_id):
    episode = VideoSyncEpisode.objects.get(pk=episode_id)
    convert = PodcastConverter(episode)
    src = convert.create_preview()
    episode.preview_path = src
    episode.save()


@app.task
def upload_video(episode_id):
    try:
        episode = VideoSyncEpisode.objects.get(pk=episode_id)
        episode.update_sync_status({
            'event': 'UPLOAD_VIDEO',
            'timestamp': arrow.utcnow().isoformat()
        })

        client = GoogleClient()
        access_token = client.get_access_token(episode.podcast)
        youtube = client.get_authenticated_service(access_token)

        episode.update_sync_status({
            'event': 'GET_ACCESS_TOKEN',
            'timestamp': arrow.utcnow().isoformat()
        })

        convert = PodcastConverter(episode)
        convert.create_video(youtube)

        if episode.youtube_id:
            send_mail(
                'Your podcast is available on YouTube! %s' % episode.podcast.name,
                '%s\n\nBy: %s' % (episode.youtube_url, episode.podcast.user.email),
                '%s Bot <%s>' % (GLOBAL_STRINGS['site_name'], GLOBAL_STRINGS['contact_email']),
                [episode.podcast.user.email],
                fail_silently=True,
            )
    except Exception as e:
        episode.upload_status = 'F'
        episode.save()

        episode.update_sync_status({
            'event': 'FAILED',
            'timestamp': arrow.utcnow().isoformat()
        })

        message = 'An error occurred while processing the video.\nError: {}'.format(
            str(e)
        )
        send_mail(
            'We are unable to generate a video for %s' % episode.podcast.name,
            message,
            '%s Bot <%s>' % (GLOBAL_STRINGS['site_name'], GLOBAL_STRINGS['contact_email']),
            [settings.DEVELOPER_EMAIL],
            fail_silently=True,
        )
