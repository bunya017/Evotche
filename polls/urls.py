from django.conf.urls import url

from . import views



app_name = 'polls'
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^vote/success/$', views.vote_success, name='vote_success'),
	url(r'^pricing/$', views.pricing, name='pricing'),
	url(r'^vote/(?P<ballot_url>[-\w]+)/$', views.vote, name='vote'),
	url(r'^submit-vote/(?P<ballot_url>[-\w]+)/$', views.new_vote, name='new_vote'),
	url(r'^privacy-policy/$', views.privacy, name='privacy'),
	url(r'^terms-of-service/$', views.terms, name='terms'),
	url(r'^results/$', views.results, name='results'),
	url(r'^results/(?P<ballot_url>[-\w]+)/$', views.ballot_results, name='ballot_results'),
	url(r'^new-category/(?P<ball_id>[0-9]+)/$', views.add_new_caty, 
			name='add_new_caty'),
	url(r'^new-choice/(?P<cat_id>[0-9]+)/$', views.add_new_choice, 
			name='add_new_choice'),
	url(r'^new-ballot/$', views.add_new_ballot, name='add_new_ballot'),
	url(r'^ballots/$', views.ballot, name='ballot'),
	url(r'^ballot/(?P<ball_id>[0-9]+)/$', views.category_view, name='category_view'),
	url(r'^category/(?P<cat_id>[0-9]+)/$', views.choice_view, name='choice_view'),
	url(r'^delete/ballot/(?P<ball_id>[0-9]+)/$', views.delete_ballot, name='delete_ballot'),
	url(r'^delete/ballot/confirm/(?P<ball_id>[0-9]+)/$', views.confirm_ballot, name='confirm_ballot'),
	url(r'^delete/category/(?P<cat_id>[0-9]+)/$', views.delete_caty, name='delete_caty'),
	url(r'^delete/category/confirm/(?P<cat_id>[0-9]+)/$', views.confirm_caty, name='confirm_caty'),
	url(r'^delete/choice/(?P<ch_id>[0-9]+)/$', views.delete_choice, name='delete_choice'),
	url(r'^delete/choice/confirm/(?P<ch_id>[0-9]+)/$', views.confirm_choice, name='confirm_choice'),
	url(r'^show-results/(?P<ballot_url>[-\w]+)/$', views.show_results_public, name='show_results'),
	url(r'^edit/(?P<ch_id>[-\w]+)/$', views.add_votes, name='add_votes'),
	url(r'^check-status/$', views.check_login_then_logout, name='check_login_then_logout'),
]