# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-16 08:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='is_token',
            field=models.BooleanField(default=True),
        ),
    ]
