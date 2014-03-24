from django.conf.urls import patterns, url

import api.views

urlpatterns = patterns('',
		url(r'^get_game_data/(\d{8})$', api.views.game_request),
		url(r'^get_game_list/$', api.views.game_list_request),
		url(r'^get_game_list/([a-zA-Z]{3})$', api.views.game_list_request)
	)