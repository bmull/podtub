from videosync.models import VideoSyncPodcast, VideoSyncEpisode

def sync_episodes(videosync_podcast):
    videosync_episodes = []
    related_podcast = videosync_podcast.related_podcast_object
    episodes_to_sync = related_podcast.episode_set.filter(videosyncepisode__isnull=True)
    for episode in episodes_to_sync:
        print('creating episode from %s' % episode)
        videosync_episode = VideoSyncEpisode.objects.create(
            id = episode.id,
            text = episode.name,
            number = episode.number,
            image_path = episode.image_path,
            related_episode_object = episode,
            podcast = videosync_podcast,
        )
        videosync_episodes.append(videosync_episode)
    return videosync_episodes

def create_related_podcast(podcast):

    if podcast.primary_color:
        COLOR = podcast.primary_color
    else:
        COLOR = '#135FA9'

    print('creating podcast from %s' % podcast)

    # Create Artwork Podcast
    videosync_podcast = VideoSyncPodcast.objects.create(
        id = podcast.id,
        user = podcast.user,
        name = podcast.name,
        slug = podcast.slug,
        image_path = podcast.image_path,
        logo_path = podcast.logo_path,
        font_name = podcast.font_name_header_text,
        primary_color = COLOR,
        related_podcast_object = podcast
    )
    print('created %s' % videosync_podcast)

    print('now to create episodes')
    videosync_episodes = sync_episodes(videosync_podcast)

    return videosync_podcast, videosync_episodes
