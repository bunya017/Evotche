# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Token, Profile



class TokenAdmin(admin.ModelAdmin):
	list_display = ['user', 'ballot_paper', 'is_used']


class ProfileAdmin(admin.ModelAdmin):
	list_display = ['user', 'organization', 'phone']


admin.site.register(Token, TokenAdmin)
admin.site.register(Profile, ProfileAdmin)