# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-24 23:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0020_auto_20180419_2122'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ballotpaper',
            name='valid_from',
        ),
        migrations.RemoveField(
            model_name='ballotpaper',
            name='valid_to',
        ),
        migrations.AddField(
            model_name='ballotpaper',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ballotpaper',
            name='start_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ballotpaper',
            name='stop_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ballotpaper',
            name='stop_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
