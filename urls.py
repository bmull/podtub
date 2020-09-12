from django.urls import path
from . import views

urlpatterns = [

    path('youtube/callback/', views.OAuthCallBack.as_view(), name='oauth_callback'),
    path('dashboard/<slug:slug>/youtube/connect/', views.YouTubeConnect.as_view(), name='youtube_connect'),
    path('dashboard/<slug:slug>/youtube/channels/', views.YouTubeChannelList.as_view(), name='youtube_channels'),
    path('dashboard/<slug:slug>/youtube/channels/set/', views.YouTubeChannelSet.as_view(), name='youtube_channels_set'),

    # confirm name, basic info for podcast
    path('dashboard/<slug:slug>/tube/setup/', views.VideoSyncSetupPodcastPage.as_view(), name='videosync_setup_podcast_page'),
    path('dashboard/<slug:slug>/tube/edit/', views.VideoSyncPodcastUpdatePage.as_view(), name='videosync_podcast_update_page'),

    path('dashboard/<slug:slug>/tube/episodes/', views.VideoSyncEpisodeListPage.as_view(), name='videosync_episode_list_page'),
    path('dashboard/<slug:podcast_slug>/tube/episodes/new/', views.VideoSyncEpisodeCreatePage.as_view(), name='videosync_episode_create_page'),
    path('dashboard/<slug:podcast_slug>/tube/episodes/<int:pk>/', views.VideoSyncEpisodeTemplatesPage.as_view(), name='videosync_episode_templates_page'),
    path('dashboard/<slug:podcast_slug>/tube/episodes/<int:pk>/edit/', views.VideoSyncEpisodeUpdatePage.as_view(),
    name='videosync_episode_update_page'),
    path('dashboard/<slug:podcast_slug>/tube/episodes/<int:pk>/tube/upload/', views.VideoSyncEpisodeUpload.as_view(),
    name='videosync_episode_upload'),

    path('image-proxy/', views.ImageProxy.as_view(), name='image_proxy'),
    path('api/youtube/upload/', views.YouTubeUploadApi.as_view(), name='youtube_upload_api'),
    path('api/video/', views.VideoSyncEpisodeCreateVideoApi.as_view(), name='video_create_api'),
    path('api/podcast/<int:podcast_id>/blur-image/', views.ImageProcessApi.as_view(), name='blur_image_api'),
]
