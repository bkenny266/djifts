from django.conf.urls import patterns, url

import api.views

urlpatterns = patterns('',
		url(r'^get_game_data/(\d+)$', api.views.game_request),
		url(r'^get_game_list/$', api.views.game_list_request),
		url(r'^get_game_list/([a-zA-Z]+)$', api.views.game_list_request)
	)