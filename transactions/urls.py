from django.conf.urls import include, url
from . import views



app_name = 'trxns'
urlpatterns = [
	url(r'^pay/(?P<ref_code>[0-9a-zA-Z ]+)/$', views.pay, name='pay'),
	url(r'^invoices/$', views.invoice_list, name='invoice_list'),
	url(r'^invoices/(?P<ref_code>[-\w]+)/$', views.get_invoice, name='get_invoice'),
	url(r'^buy-tokens/(?P<ballot_url>[-\w]+)/$', views.buy_tokens, name='buy_tokens'),
	url(r'^refresh-purchase/(?P<ref_code>[-\w]+)/$', views.refresh_purchase, name='refresh_purchase'),
]