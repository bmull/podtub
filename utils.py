import io
import os
import arrow
import math
import re
import base64
import httplib2
import requests
import subprocess
import imageio
import numpy as np
import moviepy.editor as mpe
import uuid
import boto3

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from tempfile import TemporaryFile, NamedTemporaryFile

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from googleapiclient.discovery import build
from oauth2client.client import AccessTokenCredentials
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload

from PIL import Image, ImageEnhance, ImageFilter
from pydub import AudioSegment
from pydub.playback import play
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

from videosync.models import VideoSyncEpisode, VideoSyncPodcast

SUBPROCESS_TIMEOUT = 1800
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
FPS = 1

def create_blurred_image(podcast_id):
    podcast = VideoSyncPodcast.objects.get(pk=podcast_id)

    response = requests.get(podcast.image_path)
    img = Image.open(io.BytesIO(response.content))
    blurred_image = img.filter(ImageFilter.GaussianBlur(radius=10))
    enhancer = ImageEnhance.Brightness(blurred_image)
    enhanced_im = enhancer.enhance(0.5)

    object_name = 'artwork-blur.{}'.format(img.format.lower())

    image_obj = S3Image().upload(
        enhanced_im,
        format=img.format,
        dir_name=str(podcast.id),
        object_name=object_name
    )
    podcast.blur_image_path = image_obj['url']
    podcast.save()
    return image_obj['url']

class GoogleClient(object):
    def __init__(self,
        client_id=settings.GOOGLE_CLIENT_ID,
        secret_key=settings.GOOGLE_SECRET_KEY,
        redirect_uri=settings.GOOGLE_REDIRECT_URL):

        self.client_id = client_id
        self.secret_key = secret_key
        self.redirect_uri = redirect_uri
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube',
            'https://www.googleapis.com/auth/userinfo.email'
        ]

    def get_auth_url(self):
        params = [
            'client_id=' + self.client_id,
            'redirect_uri=' + self.redirect_uri,
            'scope=' + ' '.join(self.scopes),
            'access_type=offline',
            'response_type=code'
        ]
        return 'https://accounts.google.com/o/oauth2/auth?' + '&'.join(params)

    def exchange_code(self, code):
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.secret_key,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        url = 'https://oauth2.googleapis.com/token'
        res = requests.post(url, data=data)
        return res.json()

    def validate_token(self, token):
        r = requests.post('https://www.googleapis.com/oauth2/v2/tokeninfo', data={
            'access_token': token
        })
        res = r.json()

        if 'expires_in' in res:
            if res['expires_in'] < 1000:
                return 'refresh'
            else:
                return 'valid'

        return 'invalid'

    def get_access_token(self, videosyncpodcast):
        access_token = videosyncpodcast.youtube_access_token
        status = self.validate_token(access_token)

        if status == 'refresh' or (status == 'invalid' and videosyncpodcast.youtube_refresh_token):
            return self.refresh_token(videosyncpodcast)
        elif status == 'valid':
            return access_token
        else:
            return None

    def refresh_token(self, videosyncpodcast):
        data = {
            'client_id': self.client_id,
            'client_secret': self.secret_key,
            'refresh_token': videosyncpodcast.youtube_refresh_token,
            'grant_type': 'refresh_token'
        }
        url = 'https://oauth2.googleapis.com/token'
        r = requests.post(url, data=data)
        res = r.json()

        if 'access_token' in res:
            videosyncpodcast.youtube_account.access_token = res['access_token']
            videosyncpodcast.youtube_account.save()
            return videosyncpodcast.youtube_access_token

        return None

    def get_authenticated_service(self, access_token, service='youtube', version='v3'):
        credentials = AccessTokenCredentials(access_token=access_token, user_agent='Podcast')
        return build(service, version, cache_discovery=False, http=credentials.authorize(httplib2.Http()))

def log(message, prnt=True):
    if prnt:
        print(message)

class PodcastConverter():
    def __init__(self, videosyncepisode=None):
        self.videosyncepisode = videosyncepisode
        self.episode = videosyncepisode.related_episode_object
        self.podcast = self.episode.podcast
        self.audio_url = self.episode.content_path

        self.output_video = str(self.episode.id) + '.mp4'
        self.base_dir = 'media/{}/{}'.format(self.podcast.user.pk, self.podcast.pk)
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        self.fs = FileSystemStorage(location=self.base_dir)

    def upload_video(self, youtube, video_file):
        log('upload_video', prnt=True)
        video_id = None

        try:
            service = YouTubeUpload()
            video_id = service.initialize_upload(youtube, video_file, self.videosyncepisode.text, self.episode.summary, privacy_status='unlisted')

            if video_id:
                self.videosyncepisode.upload_status = 'S'
                self.videosyncepisode.youtube_id = video_id
            else:
                self.videosyncepisode.upload_status = 'F'
        except Exception as e:
            self.videosyncepisode.upload_status = 'F'

        self.videosyncepisode.save()
        return video_id

    def check_artwork(self, local=False):
        log('Checking artwork', prnt=True)
        if local:
            image_name = str(self.episode.id) + '.png'
            image_path = os.path.join(self.base_dir, image_name)
            return os.path.exists(image_path)
        else:
            key = str(self.podcast.pk) + '/' + str(self.episode.id) + '.png'
            return S3Image().key_exists(key)


    def save_image(self, data):
        self.videosyncepisode.update_sync_status({
            'event': 'SAVE_IMAGE',
            'timestamp': arrow.utcnow().isoformat()
        })

        image_name = str(self.episode.id) + '.png'

        dataUrlPattern = re.compile('data:image/(png|jpeg);base64,(.*)$')
        image_data = dataUrlPattern.match(data).group(2)
        encoded_image_data = image_data.encode()
        image_data_b64 = base64.b64decode(encoded_image_data)

        img = Image.open(io.BytesIO(image_data_b64))
        img = self.prepare_image(img)

        image_obj = S3Image().upload(
            img,
            format='PNG',
            dir_name=str(self.podcast.id),
            object_name=image_name
        )

        self.videosyncepisode.artwork_path = image_obj['url']
        self.videosyncepisode.save()

        self.videosyncepisode.update_sync_status({
            'event': 'SAVE_IMAGE_END',
            'timestamp': arrow.utcnow().isoformat()
        })

        return img

    def create_preview(self):
        log('create_preview', prnt=True)
        try:
            audio_file = self.download_podcast(preview=True)
            clip_url = self.create_silent_video(audio_file, preview=True)
            return clip_url
        except Exception as e:
            print(e)
            return None

    def create_video(self, youtube):
        log('create_video', prnt=True)
        try:
            # audio_file = self.download_podcast()
            clip_url = self.create_silent_video(youtube)
            return clip_url
            log("Done", prnt=True)
        except Exception as e:
            print(e)

    def download_podcast(self, preview=False):
        log('download_podcast', prnt=True)
        self.videosyncepisode.update_sync_status({
            'event': 'DOWNLOAD_EPISODE',
            'timestamp': arrow.utcnow().isoformat()
        })
        try:
            with TemporaryFile() as tf:
                r = requests.get(self.audio_url, stream=True)
                for chunk in r.iter_content(chunk_size=4096):
                    tf.write(chunk)
                tf.seek(0)

                service = S3AudioVideo()
                audio_file = File(tf)
                if not self.videosyncepisode.audio_path:
                    audio_obj = service.upload(File(tf), self.podcast, self.episode, preview=preview)
                    if not preview:
                        self.videosyncepisode.audio_path = audio_obj['url']
                        self.videosyncepisode.save()

                        self.videosyncepisode.update_sync_status({
                            'event': 'DOWNLOAD_EPISODE_SUCCESS',
                            'timestamp': arrow.utcnow().isoformat()
                        })

            with TemporaryFile() as tf:
                r = requests.get(self.audio_url, stream=True)
                for chunk in r.iter_content(chunk_size=4096):
                    tf.write(chunk)
                tf.seek(0)
                song = AudioSegment.from_file(File(tf), format='mp3')

                return song[0:15000] if preview else song

        except Exception as e:
            log('download_podcast', prnt=True)
            print(e)
            return None

    def prepare_image(self, img):
        try:
            width = 1280
            height = 720

            width = 858
            height = 480

            wpercent = (width / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((width, height), Image.ANTIALIAS)
            return img
        except Exception as e:
            print(e)
            return None

    def create_silent_video(self, youtube=None, preview=False):
        log("Creating silent video", prnt=True)

        base_path = str(self.podcast.id) + '/' + str(self.episode.id)
        video_path = base_path + '.mp4'

        with NamedTemporaryFile(suffix='.mp4') as tf:
            with NamedTemporaryFile(suffix='.mp3') as _audio:
                self.videosyncepisode.update_sync_status({
                    'event': 'DOWNLOAD_AUDIO',
                    'timestamp': arrow.utcnow().isoformat()
                })
                r = requests.get(self.audio_url, stream=True)
                for chunk in r.iter_content(chunk_size=4096):
                    _audio.write(chunk)
                _audio.seek(0)
                song = AudioSegment.from_file(File(_audio), format='mp3')

                sound_length = math.ceil(len(song) / 1000)

                self.videosyncepisode.update_sync_status({
                    'event': 'CREATE_VIDEO',
                    'timestamp': arrow.utcnow().isoformat()
                })
                clip = ImageClip(self.videosyncepisode.artwork_path, duration=sound_length)
                clip.write_videofile(tf.name, fps=1, audio=_audio.name)

                self.videosyncepisode.update_sync_status({
                    'event': 'UPLOAD_VIDEO',
                    'timestamp': arrow.utcnow().isoformat()
                })
                video_id = self.upload_video(youtube, tf.name)

                return video_id

        return None

class YouTubeUpload():
    def initialize_upload(self, youtube, video_file, title, description, tags=[], category='22', privacy_status='public'):
        body=dict(
            snippet=dict(
                title=title,
                description=description,
                tags=tags,
                categoryId=category
            ),
            status=dict(
                privacyStatus=privacy_status
            )
        )

        # Call the API's videos.insert method to create and upload the video.
        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            # The chunksize parameter specifies the size of each chunk of data, in
            # bytes, that will be uploaded at a time. Set a higher value for
            # reliable connections as fewer chunks lead to faster uploads. Set a lower
            # value for better recovery on less reliable connections.
            #
            # Setting "chunksize" equal to -1 in the code below means that the entire
            # file will be uploaded in a single HTTP request. (If the upload fails,
            # it will still be retried where it left off.) This is usually a best
            # practice, but if you're using Python older than 2.6 or if you're
            # running on App Engine, you should set the chunksize to something like
            # 1024 * 1024 (1 megabyte).
            media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
        )

        return self.resumable_upload(insert_request)

    # This method implements an exponential backoff strategy to resume a
    # failed upload.
    def resumable_upload(self, insert_request):
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print("Uploading file...")
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        return response['id']
                    else:
                        exit("The upload failed with an unexpected response: %s" % response)
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                        e.content)
                else:
                    raise
            except RETRIABLE_EXCEPTIONS as e:
                error = "A retriable error occurred: %s" % e

            if error is not None:
                retry += 1
                if retry > MAX_RETRIES:
                    exit("No longer attempting to retry.")

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print("Sleeping %f seconds and then retrying..." % sleep_seconds)
                time.sleep(sleep_seconds)

class S3Service():
    def __init__(self):
        self.s3_client = boto3.client('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.s3_resource = boto3.resource('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    def key_exists(self, key):
        try:
            self.s3_resource.Object(self.bucket, key).load()
            return True
        except Exception as e:
            return False

    def open(self, object_name, bucket=settings.AWS_STORAGE_BUCKET_NAME):
        location = self.s3_client.get_bucket_location(Bucket=bucket)['LocationConstraint']
        if location:
            url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, object_name)
        else:
            url = "https://%s.s3.amazonaws.com/%s" % (bucket, object_name)
        return url

class S3Image(S3Service):
    def upload(self, pil_image, format='JPEG', dir_name=None, object_name=None):
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = str(uuid.uuid4())

        in_mem_file = io.BytesIO()
        pil_image.save(in_mem_file, format=format)
        in_mem_file.seek(0)

        final_path = object_name
        if dir_name:
            final_path = dir_name + '/' + object_name

        try:
            response = self.s3_client.upload_fileobj(in_mem_file, self.bucket, final_path)
            self.s3_resource.ObjectAcl(self.bucket, final_path).put(ACL='public-read')
        except Exception as e:
            print(str(e))
            return None

        return {
            'object_name': object_name,
            'url': self.open_image(final_path)
        }

    def open_image(self, object_name, bucket=settings.AWS_STORAGE_BUCKET_NAME):
        return self.open(object_name)

class S3AudioVideo(S3Service):
    def upload(self, media, podcast, episode, extension='.mp3', preview=False):
        object_name = str(podcast.id) + '/' + str(episode.id) + extension
        if preview:
            object_name = object_name.replace(extension, '-preview{}'.format(extension))

        try:
            response = self.s3_client.upload_fileobj(media, self.bucket, object_name)
            self.s3_resource.ObjectAcl(self.bucket, object_name).put(ACL='public-read')
        except Exception as e:
            print(str(e))
            return None

        return {
            'object_name': object_name,
            'url': self.open(object_name)
        }
