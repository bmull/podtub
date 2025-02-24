# Generated by Django 3.0.5 on 2020-07-13 17:55

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('videosync', '0006_videosyncepisode_preview_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videosyncpodcast',
            name='primary_color',
            field=colorfield.fields.ColorField(blank=True, default=None, help_text='Highlight color in images. Example: #333333', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='videosyncpodcast',
            name='secondary_color',
            field=colorfield.fields.ColorField(blank=True, default='#FFFFFF', help_text='Alternative color in images. Example: #FFFFFF', max_length=18, null=True),
        ),
    ]
