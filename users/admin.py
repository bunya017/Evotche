# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Token



class TokenAdmin(admin.ModelAdmin):
	list_display = ['user', 'ballot_paper', 'is_used']

admin.site.register(Token, TokenAdmin)