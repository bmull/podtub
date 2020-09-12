from django.db import migrations, models

def add_hash_to_color(apps, schema_editor):
    VideoSyncPodcast = apps.get_model('videosync', 'VideoSyncPodcast')
    for row in VideoSyncPodcast.objects.all():
        if row.primary_color or row.secondary_color:
            if row.primary_color and '#' not in row.primary_color:
                print('%(color)s -> #%(color)s' % {'color': row.primary_color})
                row.primary_color = '#%s' % row.primary_color
            if row.secondary_color and '#' not in row.secondary_color:
                print('%(color)s -> #%(color)s' % {'color': row.secondary_color})
                row.secondary_color = '#%s' % row.secondary_color
            row.save(update_fields=['primary_color', 'secondary_color'])

class Migration(migrations.Migration):

    dependencies = [
        ('videosync', '0007_auto_20200713_1055'),
    ]

    operations = [
        migrations.RunPython(add_hash_to_color, reverse_code=migrations.RunPython.noop),
    ]
