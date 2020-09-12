import requests

from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View, DetailView
from django.views.generic.base import RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse
from django.core.mail import send_mail
from django import forms
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from redwoodlabs.mixins import FilterQuerySetByUserMixin
from identity.strings import GLOBAL_STRINGS

from dashboard.models import Podcast, Episode

from videosync.templates import get_templates, get_episode_template
from videosync.models import YouTubeAccount, VideoSyncPodcast, VideoSyncEpisode
from videosync.logic import create_related_podcast, sync_episodes
from videosync.utils import GoogleClient, PodcastConverter, S3Image, create_blurred_image
from videosync.tasks import create_video, upload_video, create_preview

# ONBOARDING

def url2yield(url, blur=0, chunksize=1024):
   s = requests.Session()
   response = s.get(url, stream=True)

   chunk = True
   while chunk :
      chunk = response.raw.read(chunksize)

      if not chunk:
         break

      yield chunk

class ImageProxy(View):
    def get(self, request, *args, **kwargs):
        url = request.GET.get('url')
        return StreamingHttpResponse(url2yield(url), content_type="image/jpeg")

class YouTubeConnect(LoginRequiredMixin, View):
    def get(self, request, slug, *args, **kwargs):
        request.session['podcast'] = slug
        client = GoogleClient()
        return redirect(client.get_auth_url())

class OAuthCallBack(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        slug = None

        try:
            slug = request.session['podcast']
        except:
            return redirect('/')

        code = request.GET.get('code', None)
        client = GoogleClient()

        if code:
            access = client.exchange_code(code)

            if 'access_token' in access:

                videosyncpodcast = VideoSyncPodcast.objects.get(slug=slug)

                user_info_service = client.get_authenticated_service(access['access_token'], service='oauth2', version='v2')
                youtube_account = None

                try:
                    user_info = user_info_service.userinfo().get().execute()
                    youtube_account, created = YouTubeAccount.objects.get_or_create(
                        email=user_info['email'],
                        youtube_id=user_info['id']
                    )
                except Exception as e:
                    print('An error occurred: %s', e)

                if youtube_account:
                    youtube_account.access_token = access['access_token']
                    youtube_account.refresh_token = access['refresh_token']
                    youtube_account.save()

                    videosyncpodcast.youtube_account = youtube_account
                    videosyncpodcast.save()

                    return redirect('youtube_channels', slug)

        return redirect('videosync_episode_list_page', slug)

class YouTubeChannelList(LoginRequiredMixin, FilterQuerySetByUserMixin, DetailView):
    model = VideoSyncPodcast
    template_name = 'videosync/videosync_channel_list_page.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            podcast = self.get_object()
        except Exception as e:
            return redirect('videosync_setup_podcast_page', slug=self.kwargs['slug'])

        if not podcast.youtube_account and podcast.youtube_account.access_token:
            return redirect('youtube_connect', slug=self.kwargs['slug'])

        return super().dispatch(request, *args, **kwargs)

    def get_channels(self):
        client = GoogleClient()
        access_token = client.get_access_token(self.object)
        youtube = client.get_authenticated_service(access_token)
        res = youtube.channels().list(part='snippet', mine=True).execute()
        if 'items' in res:
            return res['items']
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = self.get_channels()
        context['page_title'] = "YouTube Channels"
        context['podcast'] = self.object.related_podcast_object

        return context

class YouTubeChannelSet(LoginRequiredMixin, FilterQuerySetByUserMixin, View):
   def post(self, request, *args, **kwargs):
        podcast = get_object_or_404(VideoSyncPodcast, slug=kwargs['slug'])
        podcast.youtube_channel_id = request.POST.get('channel_id', '')
        podcast.youtube_channel_name = request.POST.get('channel_name', '')
        podcast.save()
        return redirect('videosync_episode_list_page', kwargs['slug'])

class VideoSyncEpisodeCreateVideoApi(LoginRequiredMixin, View):
   def post(self, request, *args, **kwargs):
        episode = get_object_or_404(VideoSyncEpisode, id=request.POST.get('episode'))
        if not episode.youtube_id:
            try:
                convert = PodcastConverter(episode)

                if convert.check_artwork():
                    convert.prepare_resources()
                    src = convert.create_preview()
                    episode.preview_path = src
                    episode.save()
                    return JsonResponse({'src': src}, status=200)
                else:
                    return JsonResponse({ 'error': 'Artwork not found.' }, status=404)

            except Exception as e:
                return JsonResponse({ 'error': str(e) }, status=500)

        return JsonResponse({}, status=200)

class YouTubeUploadApi(LoginRequiredMixin, View):
   def post(self, request, *args, **kwargs):
        episode = get_object_or_404(VideoSyncEpisode, id=request.POST.get('episode'))
        if not episode.youtube_id:
            try:
                upload_video.delay(episode.id)
                episode.upload_status = 'P'
                episode.save()
            except Exception as e:
                return JsonResponse({ 'error': str(e) }, status=500)

        return JsonResponse({ 'videoId': episode.youtube_id }, status=200)

class ImageProcessApi(LoginRequiredMixin, View):
    def get(self, request, podcast_id):
        podcast = VideoSyncPodcast.objects.get(pk=podcast_id)
        if not podcast.blur_image_path:
            url = create_blurred_image(podcast_id)
        else:
            url = podcast.blur_image_path
        return JsonResponse({ 'imageUrl': url }, status=200)

# Normally - View to create a podcast. Then...

class VideoSyncSetupPodcastPage(LoginRequiredMixin, UpdateView):
    model = VideoSyncPodcast
    fields = ['name', 'image_path', 'logo_path', 'primary_color', ]
    template_name = 'dashboard/onboarding/onboarding_form.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            # See if it exists
            self.get_object()
        except Exception as e:
            # If not, create a new record from the related podcast
            podcast = get_object_or_404(Podcast, slug=kwargs['slug'])
            related_podcast, related_episodes = create_related_podcast(podcast)
            return redirect(self.request.path)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if not self.object:
            print('no object')
        context = super().get_context_data(**kwargs)
        context['page_emoji'] = "🎙"
        context['page_title'] = "Let's get you set up."
        context['page_subtitle'] = "First, confirm some basics for your podcast. This will help us make the design templates relevant for you."
        return context

    def get_success_url(self, **kwargs):
        return reverse('videosync_episode_list_page', kwargs={'slug':self.kwargs['slug']})


class VideoSyncPodcastUpdatePage(LoginRequiredMixin, FilterQuerySetByUserMixin, UpdateView):
    model = VideoSyncPodcast
    fields = ['name', 'image_path', 'logo_path', 'primary_color', 'secondary_color', 'font_name' ]
    template_name = 'dashboard/onboarding/onboarding_form.html'

    def get_success_url(self, **kwargs):
        if 'redirect' in self.request.GET:
            return self.request.GET['redirect']
        return self.object.get_absolute_url()


class VideoSyncEpisodeListPage(LoginRequiredMixin, FilterQuerySetByUserMixin, DetailView):
    model = VideoSyncPodcast
    template_name = 'videosync/videosync_episode_list_page.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            # See if the podcast exists yet. If not, send them to the setup process
            podcast = self.get_object()
            sync_episodes(podcast)

            # If podcast exists, check if it has any episode artwork. If not, send to create first
            episodes = podcast.get_episodes()
            if not episodes:
                return redirect('videosync_episode_create_page', podcast_slug=self.kwargs['slug'])

        except Exception as e:
            return redirect('videosync_setup_podcast_page', slug=self.kwargs['slug'])

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = self.object.get_episodes()
        context['page_title'] = "Episode VideoSync"
        context['podcast'] = self.object.related_podcast_object
        context['cta'] = {
            'label': 'Add New Episode',
            'url': reverse('videosync_episode_create_page', kwargs={'podcast_slug':self.kwargs['slug']}),
        }
        return context


class VideoSyncEpisodeCreatePage(LoginRequiredMixin, CreateView):
    model = VideoSyncEpisode
    fields = ['text', 'number', 'image_path' ] #'season',
    template_name = 'dashboard/onboarding/onboarding_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        podcast = get_object_or_404(VideoSyncPodcast, slug=self.kwargs['podcast_slug'], user=self.request.user)
        context['page_title'] = "Create new episode artwork for %s" % podcast.name
        context['page_subtitle'] = "If you don't this info yet, that's fine. You can add it later. This isn't your episode list for Podpage."
        return context

    def get_form(self):
        form = super(VideoSyncEpisodeCreatePage, self).get_form()
        form.fields['text'].widget = forms.TextInput(attrs={'placeholder': 'e.g. Bill Gates or Talking about the Stock Market'})
        form.fields['number'].widget = forms.TextInput(attrs={'placeholder': '54'})
        return form

    def form_valid(self, form):
        podcast = get_object_or_404(VideoSyncPodcast, slug=self.kwargs['podcast_slug'], user=self.request.user)
        form.instance.podcast = podcast
        previous_artwork = podcast.videosyncepisode_set.last()
        if previous_artwork:
            form.instance.template = previous_artwork.template
        return super().form_valid(form)


class VideoSyncEpisodeUpdatePage(LoginRequiredMixin, FilterQuerySetByUserMixin, UpdateView):
    model = VideoSyncEpisode
    user_field = 'podcast__user'
    fields = ['text', 'number', 'image_path' ] #'season',
    template_name = 'dashboard/onboarding/onboarding_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Edit Episode Info"
        return context

    def get_success_url(self, **kwargs):
        if 'redirect' in self.request.GET:
            return self.request.GET['redirect']
        return self.object.get_absolute_url()


class VideoSyncEpisodeUpload(LoginRequiredMixin, FilterQuerySetByUserMixin, DetailView):
    model = VideoSyncEpisode
    template_name = 'videosync/videosync_upload_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Upload Episode To YouTube"
        context['episode'] = self.object
        context['saved_template'] = get_episode_template(self.object.podcast, self.object)
        context['image_url'] = S3Image().open_image(self.object.artwork_path)

        return context


class VideoSyncEpisodeTemplatesPage(LoginRequiredMixin, FilterQuerySetByUserMixin, UpdateView):
    model = VideoSyncEpisode
    user_field = 'podcast__user'
    fields = ['template',]
    template_name = 'videosync/videosync_episode_templates_page.html'

    def get_initial(self):
        initial = super().get_initial()
        if 't' in self.request.GET:
            initial['template'] = self.request.GET['t']
        return initial

    def get_form(self):
        form = super(VideoSyncEpisodeTemplatesPage, self).get_form()
        form.fields['template'].widget = forms.HiddenInput()
        return form

    def form_valid(self, form):
        episode = self.object

        image_data = self.request.POST.get('image_data', None)

        if image_data:
            convert = PodcastConverter(episode)
            convert.save_image(image_data)

        """
        # Email Brenden about choosing a template
        send_mail(
            'New artwork chosen for %s' % episode.podcast.name,
            '%s%s\n\nBy: %s' % (GLOBAL_STRINGS['site_url'], episode.get_absolute_url(), episode.podcast.user.email),
            '%s Bot <%s>' % (GLOBAL_STRINGS['site_name'], GLOBAL_STRINGS['contact_email']),
            [settings.ADMIN_EMAIL],
            fail_silently=True,
        )
        """
        output = super().form_valid(form)

        return output

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        podcast = self.object.podcast
        context['page_title'] = 'VideoSync Generator'
        context['podcast'] = podcast
        context['episode'] = self.object
        context['saved_template'] = get_episode_template(podcast, self.object)
        target_template = None
        if 't' in self.request.GET:
            target_template = self.request.GET['t']
            context['saved_template'] = None
        context['target_template'] = target_template
        context['themes'] = get_templates(podcast, self.object, target_template=target_template)
        return context

    def get_success_url(self, **kwargs):
        return reverse('videosync_episode_list_page', kwargs={'slug':self.object.podcast.slug})
