# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import PurchaseInvoice, Item


class PurchaseInvoiceAdmin(admin.ModelAdmin):
	readonly_fields  = ('user', 'ballot_paper', 'reference_code','status',
				  'due_date')
	list_display = ['date_created', 'user', 'reference_code', 'status']


class ItemAdmin(admin.ModelAdmin):
	readonly_fields = ('unit_cost', 'quantity', 'date_added')
	list_display = ['date_added', 'item']


admin.site.register(PurchaseInvoice, PurchaseInvoiceAdmin)
admin.site.register(Item, ItemAdmin)