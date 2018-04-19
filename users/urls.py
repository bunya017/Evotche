from django.conf.urls import include, url
from django.contrib.auth.views import login

from . import views



app_name = 'users'
urlpatterns = [
	url(r'^login/$', login, {'template_name': 'users/login.html'}, name='login'),
	url(r'^logout/$', views.logout_view, name='logout'),
	url(r'^signup/$', views.signup, name='signup'),
	url(r'^page/(?P<ball_url>[-\w]+)/$', views.show_ballot_page, name='show_ballot_page'),
	url(r'^userpage/(?P<ball_url>[-\w]+)/$', views.showBallotPage, name='showBallotPage'),
	url(r'^new_token/$', views.new_token, name='new_token'),
	url(r'^num_token/$', views.num_token, name='num_token'),
	url(r'^token/$', views.token_login, name='token_login'),
	url(r'^tokens/$', views.tokens_view, name='tokens_view'),
	url(r'^mytokens/(?P<ball_url>[-\w]+)/$', views.my_token, name='my_token'),
]