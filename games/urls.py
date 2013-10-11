from django.conf.urls import patterns, url

import games.views

urlpatterns = patterns('',
		url(r'^(\d+)/(home)/$', games.views.game_view),
		url(r'^(\d+)/(away)/$', games.views.game_view),
		url(r'^testbootstrap/$', games.views.test_bootstrap),
	)